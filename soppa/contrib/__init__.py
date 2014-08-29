import os, sys, copy, re, datetime, getpass, zlib, inspect
from optparse import OptionParser
from subprocess import call

from soppa import *
from soppa.internal.tools import import_string, get_full_dict, get_namespaced_class_values, fmt_namespaced_values, get_class_dict, is_configurable_property
from soppa.internal.logs import DeployLog, dlog
from soppa.internal.mixins import ApiMixin, NeedMixin, ReleaseMixin, FormatMixin
from soppa.internal.mixins import with_settings, settings#TODO: namespace under ApiMixin?
from soppa.internal.manager import PackageManager

# TODO: taken from Fabric... but str assignment on passing var is nasty, convert to being a dict internally
# python-invoke will have a proper Result object, future-proof
class AttributeString(str):
    @property
    def stdout(self):
        return str(self)

class Soppa(ApiMixin, NeedMixin, ReleaseMixin, FormatMixin):
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
        applied = {}
        def apply_vars(values, cur_values):
            r = {}
            for k,v in values.iteritems():
                if not k.startswith('__') \
                        and not callable(v) \
                        and not isinstance(v, property) \
                        and not isinstance(v, staticmethod):
                    cur_dict_value = cur_values.get(k, None)
                    cur_instance_value = getattr(self, k)
                    if not cur_dict_value and not callable(cur_instance_value):
                        setattr(self, k, v)
                        r[k] = v
            return r
        def cur_values(c):
            r = {}
            r.update(self.__dict__)
            r.update(c)
            return r
        applied.update(apply_vars(self.__class__.__dict__, cur_values=cur_values(applied)))
        applied.update(apply_vars(get_full_dict(self), cur_values=cur_values(applied)))

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

        # set initial state based on context
        for k,v in context.iteritems():
            #if not self.has_need(k) and k not in [self.get_name()]:
            if k not in [self.get_name()]:
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

    def is_deferred(self, handler):
        for rule in self.defer_handlers:
            if handler.endswith(rule) or rule=='*':
                return True
        return False

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
            rs = {}
            rs['instance'] = method
            rs['method'] = method
            rs['handler'] = '{}.{}'.format(self.get_name(), name)
            rs['modified'] = False
            dlog.add('defer', 'all', rs)
            return
        handlers = kwargs.pop('handler', [])
        for handler in handlers:
            if isinstance(handler, list):
                print "HANDLE-pre",handler
        result = method(*args, **kwargs)

        def is_dirty(result):
            return result.modified

        for handler in handlers:
            handler_instance = self.get_handler(handler)
            if isinstance(handler_instance, basestring):
                raise Exception("Class variable collision for handler {}; namespacing issue?".format(handler))
            if self.is_deferred(handler):
                rs = result.__dict__
                rs['instance'] = handler_instance
                rs['handler'] = handler
                dlog.add('defer', 'all', rs)
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
            self.soppa.local_path,
            self.soppa.local_conf_path,
            self.get_name(),
            '')

    def pre_setup(self):
        return {}

    def post_setup(self):
        return {}

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
    return None, klass
