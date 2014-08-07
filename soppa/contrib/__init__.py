import os, sys, copy, re, datetime, getpass, zlib
from optparse import OptionParser
from subprocess import call

from soppa import *
from soppa.internal.fmt import fmtkeys, formatloc, escape_bad_matches
from soppa.internal.tools import import_string
from soppa.internal.logs import DeployLog
from soppa.internal.mixins import ApiMixin, NeedMixin, InspectMixin, DeployMixin
from soppa.internal.mixins import with_settings, settings#TODO: namespace under ApiMixin?
from soppa.internal.manager import PackageManager

dlog = DeployLog()

class Soppa(DeployMixin, NeedMixin):
    reserved_keys = ['needs','reserved_keys','env']
    needs = ['soppa.release']

    def __init__(self, *args, **kwargs):
        super(Soppa, self).__init__(*args, **kwargs)
        # class(dict()) == class(ctx=dict())
        self.args = args
        self.kwargs = kwargs
        if self.args\
                and isinstance(self.args[0], dict)\
                and len(self.args)==1\
                and not self.kwargs.get('ctx'):
            self.kwargs['ctx'] = self.args[0]

        # apply class vars as instance vars for easy __dict__
        for k,v in self.__class__.__dict__.items():
            if not k.startswith('__') and not callable(v) and not isinstance(v, property):
                setattr(self, k, v)

        self.env = env # fabric
        self.soppa = SOPPA_DEFAULTS
        # Configuration
        context = {}
        # parent variables
        context.update(**kwargs.get('ctx_parent', {}))
        # instance variables
        context.update(**kwargs.get('ctx', {}))
        if any([key in self.reserved_keys for key in context.keys()]):
            raise Exception("Reserved keys used")
        # set initial state based on context, ensuring not overriding needs[]
        for k,v in context.iteritems():
            if not self.has_need(k) and k not in [self.get_name()]:
                setattr(self, k, v)

    def __getattribute__(self, key):
        """ Magic: To be able to to support 'self.foo' -- for existing variables especially -- and,
        have the returned string be formatted, this method intercepts all attribute access """
        try:
            result = object.__getattribute__(self, key)
        except Exception, e:
            # lazy-load dependencies defined in needs=[]
            if not key.startswith('__') and self.has_need(key):
                instance = self._load_need(key, alias=None, ctx={'args':self.args, 'kwargs': self.kwargs})
                name = key.split('.')[-1]
                setattr(self, name, instance)
                return instance
            raise
        if not key.startswith('_') and isinstance(result, basestring):
            result = self.fmt(result)
        return result

    def _load_need(self, key, alias=None, ctx={}):
        return self.get_and_load_need(self.find_need(key), alias=alias, ctx=ctx)

    # Properties for common needs; configured via need_X=''
    # TODO: check for in __getattribute__?
    @property
    def vcs(self):
        if not hasattr(self, '_vcs_proxy'):
            self._vcs_proxy = self._load_need(self.need_vcs, alias='vcs', ctx={'args':self.args,'kwargs':self.kwargs})
        return self._vcs_proxy

    @property
    def web(self):
        if not hasattr(self, '_web_proxy'):
            self._web_proxy = self._load_need(self.need_web, alias='web', ctx={'args':self.args,'kwargs':self.kwargs})

        return self._web_proxy

    def isDirty(self):
        dirty = False
        # has configuration for need changed?
        # TODO: read config from server for initial state
        # TODO: if never deployed, should be dirty.
        for host, data in dlog.data.get('hosts', {}).iteritems():
            if not data.get(self.get_name()):
                continue
            for outcome in data[self.get_name()].get('files', []):
                if outcome['diff']:
                    dirty = True
        return dirty

    def packman(self):
        key = 'packman'
        if not self._CACHE.get(key):
            self._CACHE[key] = PackageManager(self)
        return self._CACHE[key]

    def is_performed(self, fn):
        env.performed.setdefault(env.host_string, {})
        env.performed[env.host_string].setdefault(fn, False)
        return env.performed[env.host_string][fn]

    def set_performed(self, fn):
        self.is_performed(fn)
        env.performed[env.host_string][fn] = True

    @property
    def parent(self):
        return self.parent_instance if hasattr(self, 'parent_instance') else self

    @property
    def root(self):
        result = self
        while True:
            identifier = id(result)
            result = result.parent
            if id(result)==identifier:
                break
        return result

    def fmt(self, string, **kwargs):
        """ Format a string.
        self.fmt(string) vs string.format(self=self)
        self.fmt(string, foo=2) vs string.format(foo=2, self=self)

        Add self as formatting argument, and prefix keys with self., if key not in arguments.
        {foo} => {self.foo}.format(self=self)
        {foo} kwargs(foo=2) => {foo}.format(foo=foo)
        {foo.bar} kwargs(foo=2) => {foo}.format(self=self)

        For self.foo to equal {foo}: __getattribute__ using fmt() means can not access variables, that
        require formatting and are missing those values from the called instance.
        Defaulting to empty strings, instead of exceptions because of that.
        """
        for times in range(6):
            keys = []
            if isinstance(string, basestring):
                string = escape_bad_matches(string)
                if '{' not in string:
                    break
                keys = fmtkeys(string)
            kwargs_keys = kwargs.keys()
            for key in keys:
                if key not in kwargs_keys:
                    if not key.startswith('self.'):
                        realkey = key.split('.')[0]
                        if hasattr(self, realkey):
                            string = string.replace('{'+key+'}', '{self.'+key+'}')
                        else:
                            kwargs.setdefault(key, '')
            if '{self.' in string:
                kwargs['self'] = self
            string = string.format(**kwargs)
        return string

    def copy_configuration(self, recurse=False):
        """ Prepare local copies of module configuration files. Does not overwrite existing files. """
        if os.path.exists(self.module_conf_path()):
            self.local('mkdir -p {0}'.format(self.local_module_conf_path()))
            with self.hide('output','warnings'), settings(warn_only=True):
                if not self.local_module_conf_path().startswith(self.module_conf_path()):
                    self.local('cp -Rn {0} {1}'.format(
                        self.module_conf_path(),
                        self.local_module_conf_path(),))
        if recurse:
            for k,v in enumerate(self.get_needs()):
                v.copy_configuration()

    def module_path(self):
        return here(instance=self)

    def module_conf_path(self):
        return os.path.join(self.module_path(), self.soppa.local_conf_path, '')

    def local_module_conf_path(self):
        return os.path.join(
            self.soppa.local_project_root,
            self.soppa.local_conf_path,
            self.get_name(),
            '')

    def setup(self):
        return {}

    def configure(self):
        return {}

    def get_name(self):
        return self.__class__.__name__.lower()

    def settings(self):
        return {}

    def cli_interface(self, action=None, *args, **kwargs):
        raise Exception("TODO")

    def latest_release(self):
        rel = self.sudo("cd {basepath} && readlink www").strip()
        if rel:
            return rel.replace('releases/', '')
        return env.release

    def __unicode__(self):
        return unicode(self.get_name())

def register(klass, *args, **kwargs):
    """ Add as Fabric task, to be visible in 'fab -l' listing """
    name = klass.__name__.lower()

    fabric_task = None
    def task_instantiate():
        klass().cli_interface()

    fabric_task = task(name=name)(task_instantiate)

    return fabric_task, klass
