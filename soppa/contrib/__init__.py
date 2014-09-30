import os, sys, copy, re, datetime, getpass, zlib, inspect
from optparse import OptionParser
from subprocess import call

from soppa import *
from soppa.internal.tools import import_string, get_full_dict, get_namespaced_class_values, fmt_namespaced_values, get_class_dict, is_configurable_property
from soppa.internal.logs import DeployLog
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

    def apply_value(self, key, value):
        if self.has_need(key):
            return
        if callable(getattr(self, key, None)):
            return
        setattr(self, key, value)

    def __init__(self, ctx={}, *args, **kwargs):
        self._CACHE = {}
        self.args = args
        self.kwargs = kwargs
        self.kwargs['ctx'] = ctx
        self.log = DeployLog()
        self.context = {}
        #self.action('packages', given=lambda self: not self.is_deferred('packages'))

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
                        self.apply_value(k, v)
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
        if kwargs.get('ctx_parent'):
            parent_context = kwargs['ctx_parent']['parent_instance'].context
            # do not pass parent variables containing own namespace
            # eg. x_y + p_x_y passed for parent p; x should not receive x_y, for p_x_y to be in effect
            parent_context_clean = {}
            for k,v in parent_context.iteritems():
                if not k.startswith(self.get_name()):
                    parent_context_clean.setdefault(k, v)
            context.update(**parent_context_clean)
        # instance variables
        context.update(**kwargs.get('ctx', {}))
        self.context = context
        if any([key in self.reserved_keys for key in context.keys()]):
            raise Exception("Reserved keys used")

        # set initial state based on context
        for k,v in context.iteritems():
            if k not in [self.get_name()]:
                self.apply_value(k, v)

        if self.project is None: # default project name for project-naming convention used by ReleaseMixin
            self.project = self.get_name()

        namespaced_values = get_namespaced_class_values(self)

        # rescope configuration
        new_data = self.rescope_namespaced_variables(self.__dict__)
        for k,v in new_data.iteritems():
            self.apply_value(k, v)
        
        # pre-format all strings
        for key in self.__dict__.keys():
            value = getattr(self, key)
            if isinstance(value, basestring):
                self.apply_value(key, self.fmt(value))

        # namespace class attributes
        keys = self.__dict__.keys()
        for k,v in fmt_namespaced_values(self, namespaced_values).iteritems():
            if k not in keys:
                self.apply_value(k, v)

        # Update fabric env
        fabric_keys = ['user', 'password', 'use_sudo']
        for key in fabric_keys:
            if key in context.keys():
                setattr(env, key, context[key])

    def is_deferred(self, handler):
        for rule in self.defer_handlers:
            if handler.endswith(rule) or rule=='*':
                return True
        return False

    def action(self, name, *args, **kwargs):
        """
        Action allows wrapping commands into a context that oversees the method flow
        - when=[]; execute when True
        - handlers=[] -- ['apache.restart']; run handlers on commands
        """
        method = getattr(self, name)
        when = kwargs.pop('when', None)
        if when and not when(self):
            # TODO: log.debug()
            rs = {}
            rs['instance'] = method
            rs['method'] = method
            rs['handler'] = '{}.{}'.format(self.get_name(), name)
            rs['modified'] = False
            self.log.add('defer', 'all', rs)
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
                self.log.add('defer', 'all', rs)
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
        # TODO: - if never deployed, should be dirty.
        for host, data in self.log.data.get('hosts', {}).iteritems():
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

    def packages(self, path=None):
        pm = self.packman()
        return pm.get_packages(path=path)

    def packages_getset(self, packages):
        pm = self.packman()
        pm.write_packages(packages)
        pm.download_packages(packages)
        pm.sync_packages(packages)
        pm.install_packages(packages)

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
        """ Copy default module configuration files to project. Does not overwrite existing files. """
        if os.path.exists(self.module_conf_path()):
            with self.hide('output','warnings'), settings(warn_only=True):
                if not self.local_module_conf_path().startswith(self.module_conf_path()):
                    if not os.path.exists(self.local_module_conf_path()):
                        self.local('mkdir -p {}'.format(self.local_module_conf_path()))
                    self.local('cp -Rn {} {}'.format(
                        self.module_path(),
                        self.local_module_conf_path(),))

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
