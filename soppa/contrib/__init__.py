import os, sys, copy, re, datetime, getpass, zlib, inspect
from optparse import OptionParser
from subprocess import call

from soppa import *
from soppa.internal.fmt import fmtkeys, formatloc, escape_bad_matches
from soppa.internal.tools import import_string, get_full_dict, get_namespaced_class_values, fmt_namespaced_values
from soppa.internal.logs import DeployLog, dlog
from soppa.internal.mixins import ApiMixin, NeedMixin, InspectMixin, DeployMixin, ReleaseMixin
from soppa.internal.mixins import with_settings, settings#TODO: namespace under ApiMixin?
from soppa.internal.manager import PackageManager

# TODO: taken from Fabric... but str assignment on passing var is nasty, convert to being a dict internally
# python-invoke will have a proper Result object, future-proof
class AttributeString(str):
    @property
    def stdout(self):
        return str(self)

class Soppa(DeployMixin, NeedMixin, ReleaseMixin):
    reserved_keys = ['needs','reserved_keys','env']
    autoformat = True
    needs = []
    strict_fmt = True
    defer_handlers = []

    def __init__(self, ctx={}, *args, **kwargs):
        super(Soppa, self).__init__(*args, **kwargs)
        self.args = args
        self.kwargs = kwargs
        self.kwargs['ctx'] = ctx

        # Apply all inherited variables to have them in __dict__ scope
        # - allows to format dynamic variables -- fmt() -- instance variables in __init__
        def apply_vars(values):
            cur_values = self.__dict__
            for k,v in values.iteritems():
                if not k.startswith('__') \
                        and not callable(v) \
                        and not isinstance(v, property) \
                        and not isinstance(v, staticmethod):
                    cur_dict_value = cur_values.get(k, None)
                    cur_instance_value = getattr(self, k)
                    if not cur_dict_value and not callable(cur_instance_value):
                        setattr(self, k, v)
        apply_vars(self.__class__.__dict__)
        apply_vars(get_full_dict(self))

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

        namespaced_values = get_namespaced_class_values(self)

        if self.project is None: # default project name for project-naming convention used by ReleaseMixin
            self.project = self.get_name()

        # rescope configuration
        new_data = self.rescope_namespaced_variables(self.__dict__)
        for k,v in new_data.iteritems():
            setattr(self, k, v)
        
        # pre-format all strings
        for key in self.__dict__.keys():
            value = getattr(self, key)
            if isinstance(value, basestring):
                setattr(self, key, self.fmt(value))

        # namespace class attributes
        keys = self.__dict__.keys()
        for k,v in fmt_namespaced_values(self, namespaced_values).iteritems():
            if k not in keys:
                setattr(self, k, v)

    def __getattr__(self, key):
        try:
            result = self.__dict__[key]
        except KeyError, e:
            # lazy-load dependencies defined in needs=[]
            if not key.startswith('__') and self.has_need(key):
                instance = self._load_need(key, alias=None, ctx={'args':self.args, 'kwargs': self.kwargs})
                name = key.split('.')[-1]
                setattr(self, name, instance)
                return instance
            raise AttributeError(e)
        return result

    def _load_need(self, key, alias=None, ctx={}):
        return self.get_and_load_need(self.find_need(key), alias=alias, ctx=ctx)

    def action(self, name, *args, **kwargs):
        """
        Action allows wrapping commands into a context that oversees the method flow
        - given=[]; only execute, if True
        - handlers=[] -- ['apache.restart']; run handlers on commands
        """
        method = getattr(self, name)
        given = kwargs.pop('given', None)
        if given and not given(self):
            # TODO: log.debug()
            dlog.add('skipped', 'given', [name, args, kwargs])
            return
        handlers = kwargs.pop('handler', [])
        for handler in handlers:
            if isinstance(handler, list):
                print "HANDLE-pre",handler
        result = method(*args, **kwargs)
        def is_deferred(instance, handler):
            for rule in instance.defer_handlers:
                if handler.endswith(rule) or rule=='*':
                    return True
            return False

        def is_dirty(result):
            return result.modified

        for handler in handlers:
            handler_instance = self.get_handler(handler)
            if is_deferred(self, handler):
                dlog.add('defer', 'all', [handler, handler_instance, result.__dict__])
                continue
            # TODO: might always want restart, even if not modified?
            if is_dirty(result):
                handler_instance()
        return result

    def get_handler(self, name):
        """
        Handler: module.method
        NOTE: needs=[] provide resolution for names
        """
        module, method = name.split('.')
        if module == self.get_name():
            instance = self
        else:
            instance = getattr(self, module)
        return getattr(instance, method)

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
        """ When instance is part of needs[], return the parent. Default is self. """
        return self.parent_instance if hasattr(self, 'parent_instance') else self

    @property
    def root(self):
        """ When instance is part of needs[], return the root. Default is self. """
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

        Adds self as formatting argument, and prefix keys with self., if key not in arguments.
        {foo} => {self.foo}.format(self=self)
        {foo} kwargs(foo=2) => {foo}.format(foo=foo)
        {foo.bar} kwargs(foo=2) => {foo}.format(self=self)
        """
        for times in range(6):
            keys = []
            if isinstance(string, basestring):
                string = escape_bad_matches(string)
                if '{' not in string:
                    break
                keys = fmtkeys(string)
            else:
                return string
            kwargs_keys = kwargs.keys()
            for key in keys:
                if key not in kwargs_keys:
                    if not key.startswith('self.'):
                        realkey = key.split('.')[0]
                        if hasattr(self, realkey):
                            if self.strict_fmt and getattr(self, realkey) is None:
                                raise Exception("Undefined key: {}".format(realkey))
                            string = string.replace('{'+key+'}', '{self.'+key+'}')
                        else:
                            if not self.strict_fmt:
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

    def restart(self):
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
