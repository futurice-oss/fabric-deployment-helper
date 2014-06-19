import os, sys, copy, re
from contextlib import contextmanager
import fnmatch
import inspect

# import and prefix fabric functions to not inadvertedly use them
from fabric.api import cd as fabric_cd, local as fabric_local, run as fabric_run, sudo as fabric_sudo, task as fabric_task, put as fabric_put, execute as fabric_execute, hide as fabric_hide, lcd as fabric_lcd, get as fabric_get, put as fabric_put
from fabric.contrib.files import exists as fabric_exists
from fabric.context_managers import prefix as fabric_prefix, settings
from fabric.decorators import with_settings
from fabric.operations import prompt as fabric_prompt

from soppa import *

env.possible_bugged_strings = []
env.ctx_failure = []

from importlib import import_module
def import_string(dotted_path):
    """ Import something, eg. 'soppa.pip', or 'x.y.z' """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except (ValueError, AttributeError) as e:
        module_path = dotted_path
    try:
        return import_module(dotted_path)
    except ImportError, e:
        module = import_module(module_path)
        try:
            return getattr(module, class_name)
        except ImportError, e:
            log.debug(e)

class Upload(object):
    def __init__(self, frm, to, instance, caller_path):
        self.env = instance.get_ctx()
        self.args = (frm, to)
        self.caller_path = caller_path

        self.up()

    def find(self, path, needle):
        matches = []
        for root, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, needle):
                matches.append(os.path.join(root, filename))
        return matches

    def choose_template(self):
        filename = self.args[0].split('/')[-1]
        filepath = '{0}{1}'.format(self.caller_path, self.args[0])
        rs = []
        def wrapper(p):
            if p.startswith('/'):
                return p
            p = os.path.join(self.env['local_project_root'], p)
            return p
        for k in self.env['config_dirs']:
            rs += self.find(wrapper(k), filename)
        if rs:
            filepath = '{0}'.format(rs[0])
        return filepath

    def up(self):
        from_path = formatloc(self.args[0], self.env)
        if not from_path.startswith('/'):
            filepath = self.choose_template()
            self.args = (filepath,) + self.args[1:]

import string, copy, re, copy
def formatloc(s, ctx={}, **kwargs):
    """ Lazy evaluation for strings """
    if not isinstance(s, basestring) and not callable(s):
        return s
    if 'raw' in kwargs:
        return s
    for times in range(6):
        kw = {}
        # adds values no interpolated values with defaults
        if isinstance(s, basestring):
            kw.update(**{k[1]: '' for k in string.Formatter().parse(s) if k[1] and '.' not in k[1]})
            s = s.replace('{}','{{}}')
            if '{' not in s:
                break
        keys = kw.keys()
        for key in keys:
            kw.update({key: getattr(ctx, key, '{{{0}}}'.format(key))})

        kw.update(**ctx)
        kw.update(**kwargs)
        
        # resolve functions
        for k,v in kw.iteritems():
            if k in keys:
                if callable(v):
                    kw[k] = v(kw)
        try:
            if callable(s):
                s = s(kw)
            else:
                if isinstance(s, basestring):
                    s = s.format(**kw)
        except IndexError, e:
            print "EE",e
            raise KeyError
    return s

class LocalDict(dict):
    """ Format variables against context on return """
    def __getattr__(self, key):
        try:
            if key.startswith('__'):
                return self[key]
            return formatloc(self[key], self)
        except KeyError:
            # to conform with __getattr__ spec
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

class Soppa(object):
    # static
    soppa_modules_installed = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        # class(dict()) == class(ctx=dict())
        if self.args\
                and isinstance(self.args[0], dict)\
                and len(self.args)==1\
                and not self.kwargs.get('ctx'):
            self.kwargs['ctx'] = self.args[0]

        Soppa.soppa_modules_installed.append(self.get_name())

        self.set_context(*args, **kwargs)

    # Local extensions to Fabric
    def local_sudo(self, cmd, capture=True, **kwargs):
        """
        with bash -l virtualenv-wrapper not activate
        sudo -E required for environment variables to be passed in
        """
        cmd = cmd.replace('"','\\"').replace('$','\\$')
        return self.local('sudo -E -S -p \'sudo password:\' /bin/bash -c "{0}"'.format(cmd), capture=capture, **kwargs)

    def local_put(self, local_path, remote_path, capture=True, **kwargs):
        if kwargs.get('use_sudo'):
            return self.sudo('cp {0} {1}'.format(local_path, remote_path))
        kw = dict(
                capture=kwargs.get('capture', True),
                shell=kwargs.get('shell', None))
        return self.local('cp {0} {1}'.format(local_path, remote_path), **kw)
    local_get = local_put

    # Fabric API
    def hide(self, *groups):
        return fabric_hide(*groups)

    def sudo(self, command, *args, **kwargs):
        if env.get('local_deployment'):
            return self.local_sudo(command, *args, **kwargs)
        return fabric_sudo(self.fmt(command), *args, **kwargs)

    def run(self, command, **kwargs):
        if self.env.get('local_deployment'):
            return self.local(command, **kwargs)
        if self.env.get('use_sudo'):
            return self.sudo(command, **kwargs)
        else:
            return fabric_run(self.fmt(command), **kwargs)

    def local(self, command, capture=False, shell=None):
        return fabric_local(self.fmt(command), capture=capture, shell=shell)

    def put(self, local_path, remote_path, **kwargs):
        local_path = getattr(local_path, 'name', local_path)
        if self.env.get('local_deployment'):
            return self.local_put(self.fmt(local_path), self.fmt(remote_path), **kwargs)
        if env.get('use_sudo'):
            kwargs['use_sudo'] = True
        return fabric_put(self.fmt(local_path), self.fmt(remote_path), **kwargs)

    def get(self, remote_path, local_path, **kwargs):
        local_path = getattr(local_path, 'name', local_path)
        if self.env.get('local_deployment'):
            return self.local_get(self.fmt(remote_path), self.fmt(local_path), **kwargs)
        if env.get('use_sudo'):
            kwargs['use_sudo'] = True
        return fabric_get(self.fmt(remote_path), self.fmt(local_path), **kwargs)

    def cd(self, path):
        return fabric_cd(self.fmt(path))

    def prefix(self, command):
        return fabric_prefix(self.fmt(command))

    def exists(self, path, use_sudo=False, verbose=False):
        return fabric_exists(self.fmt(path), use_sudo=use_sudo, verbose=verbose)
    
    # END Fabric API

    @contextmanager
    def mlcd(self, path):
        """ Really move to a local directory, unlike lcd """
        calling_file = inspect.getfile(sys._getframe(2))
        d = here(path, fn=calling_file)
        try:
            yield os.chdir(d)
        finally:
            os.chdir(self.fmt('{basedir}'))

    def has_need(self, string):
        return any([re.findall(string, k) for k in self.env.needs])

    def find_need(self, string):
        for k in self.env.needs:
            if re.findall(string, k):
                return k
        return None

    def install_packages(self, recipe):
        for k,v in recipe.env.get('packages', {}).iteritems():
            print "Installing recipe packages",recipe,v
            if k=='pip':
                if isinstance(v, basestring): # requirements.txt
                    source = here(instance=recipe)
                    rpath = os.path.join(source, v)
                    self.pip.prepare_python_packages(rpath)
                elif isinstance(v, list): # list of packages
                    self.pip.prepare_python_packages(v)
                else:
                    raise Exception("unknown pip listing format")
            if k=='apt':
                if isinstance(v, basestring):
                    v = [v]
                if not env.TESTING:
                    if self.operating.is_linux():
                        self.apt.update()
                        self.apt.install(v)

    def install_all_packages(self):
        recipe = self
        self.install_packages(self)
        for recipe in self.get_needs():
            self.install_packages(recipe)
        if not self.env.TESTING:
            self.pip.synchronize_python_packages()

    def add_need(self, string):
        """ Add additional 'need' dynamically """
        self.env.setdefault('needs', [])
        self.env.needs.append(string)
        self.get_and_load_need(string)

    def fmt(self, string, **kwargs):
        """ Format a string.
        self.fmt(string) vs string.format(**self.get_ctx())
        self.fmt(string, foo=2) vs string.format(foo=2, **self.get_ctx())
        """
        ctx = self.get_ctx()
        ctx.update(**kwargs)
        result = formatloc(string, ctx)
        possible_unfilled_vars = ('{' in result)
        if possible_unfilled_vars:
            env.possible_bugged_strings.append([string,result])
        return result

    def up(self, frm, to, ctx={}):
        """ Upload a template, with arguments relative to calling path """
        caller_path = here(fn=inspect.getfile(sys._getframe(1)))
        ctx = ctx or self.get_ctx()

        upload = Upload(frm, to, instance=self, caller_path=caller_path)
        self.template.up(*upload.args, context=ctx)

    def setup(self):
        return {}

    def get_name(self):
        return self.__class__.__name__.lower()

    def set_context(self, *args, **kwargs):
        # Configuration is a layer, top to bottom:
        self.env = LocalDict()

        # global variables
        self.env.update(**env)

        # parent variables
        self.env.update(**kwargs.get('ctx_parent', {}))

        # Do not pass internal Soppa variables onward
        ignored_internal_variables = ['needs', 'packages']
        for k in ignored_internal_variables:
            if self.env.get(k):
                del self.env[k]

        # class variables
        self.env.update(**self.get_class_settings())

        # global class variables
        self.env.update(**env.ctx.get(self.get_name(), {}))

        # instance variables
        self.env.update(**kwargs.get('ctx', {}))

    def get_class_settings(self):
        rs = {}
        def is_valid(key, value):
            # TODO: only allow strings, numbers?
            if not key.startswith('__')\
                and not inspect.ismethod(value)\
                and not inspect.isfunction(value)\
                and not inspect.isclass(value):
                return True
            return False
        for key,value in self.__class__.__dict__.iteritems():
            if is_valid(key, value):
                rs[key] = value
        return rs

    def get_ctx(self, include_needs=True):
        """ Get context of instance and its dependencies """
        rs = {}
        if include_needs:
            for key in self.env.get('needs', []):
                name = key.split('.')[-1]
                try:
                    rs.update(getattr(self, name).get_ctx(include_needs=False))
                except Exception, e:
                    env.ctx_failure.append([self, key, e])
        rs.update(self.env)
        for k,v in rs.iteritems():
            rs[k] = formatloc(v, rs)
        return rs
    
    def get_needs(self):
        rs = []
        for k in self.env.get('needs', []):
            name = k.split('.')[-1]
            rs.append(getattr(self, name))
        return rs

    def settings(self):
        return {}

    def apply_settings(self, action=None):
        """ package settings are defaults, that globals can override """
        defaults = self.get_ctx()
        if defaults.get('required_settings'):
            if not all([getattr(env, k, False) for k in defaults.required_settings]):
                raise Exception("Configuration required")
        if defaults.get('actions'):
            if not action in defaults.actions:
                raise Exception("Usage: {0}:{1}".format(self.get_name(), '|'.join(defaults.actions)))

    def cli_run(self, action=None, *args, **kwargs):
        """ register() calls this function
        - for usage via fabric CLI
        """
        print "TODO: CLI RUN",action,type(action),args,kwargs

    def get_need(self, name):
        for k in self.env.get('needs', []):
            if k.endswith(name):
                return k
        return None

    def get_and_load_need(self, key, *args, **kwargs):
        # remove instance specific kwargs.ctx
        kwargs_copy = kwargs
        if kwargs_copy.get('ctx'):
            del kwargs_copy['ctx']

        # pass parent context
        kwargs_copy['ctx_parent'] = self.env

        name = key.split('.')[-1]
        module = import_string(key)
        fn = getattr(module, name)

        instance = fn(ctx_parent=self.env)
        instance.set_context(*args, **kwargs_copy)
        setattr(self, name, instance)

        return instance

    def __getattr__(self, key):
        try:
            return self.__dict__[key]
        except:
            # load dependencies lazily
            if self.has_need(key):
                return self.get_and_load_need(self.find_need(key), *self.args,
                                                                    **self.kwargs)
            raise

    def __unicode__(self):
        return unicode(self.get_name())

def register(klass, *args, **kwargs):
    """ Add as Fabric task, to be visible in 'fab -l' listing """
    name = klass.__name__.lower()

    fabric_task = None
    def task_instantiate():
        klass().cli_run()

    fabric_task = task(name=name)(task_instantiate)

    return fabric_task, klass

