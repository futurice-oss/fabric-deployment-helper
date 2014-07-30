import os, sys, copy, re
from contextlib import contextmanager
import inspect

# import and prefix fabric functions into their own namespace to not inadvertedly use them
from fabric.api import cd as fabric_cd, local as fabric_local, run as fabric_run, sudo as fabric_sudo, task as fabric_task, put as fabric_put, execute as fabric_execute, hide as fabric_hide, lcd as fabric_lcd, get as fabric_get, put as fabric_put
from fabric.contrib.files import exists as fabric_exists
from fabric.context_managers import prefix as fabric_prefix, settings
from fabric.decorators import with_settings
from fabric.operations import prompt as fabric_prompt

from soppa import *
from soppa.fmt import formatloc
from soppa.tools import import_string, Upload, LocalDict

env.possible_bugged_strings = []
env.ctx_failure = []

class Soppa(object):
    needs = []
    packages = {
            'pip': 'requirements_global.txt',
            'pip.venv': 'requirements_venv.txt',
            'apt': 'apt_global.txt',
            }
    package_handlers = {
            'pip': 'soppa.internal.packagehandler.PipPackage',
            'pip.venv': 'soppa.internal.packagehandler.PipPackage',
            'apt': 'soppa.internal.packagehandler.AptPackage',}
    reserved_keys = ['needs','packages','reserved_keys','pkg',]
    ignored_internal_variables = ['needs', 'packages']

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self._CACHE = {}
        # class(dict()) == class(ctx=dict())
        if self.args\
                and isinstance(self.args[0], dict)\
                and len(self.args)==1\
                and not self.kwargs.get('ctx'):
            self.kwargs['ctx'] = self.args[0]

        # Configuration
        context = LocalDict()
        # global fabric variables
        # - immediately evaluated against current context (slow)
        # TODO: scope to self.env, in templates {env.X} ?
        envcopy = {}
        ctx = {}
        ctx.update(**env)
        ctx.update(**kwargs.get('ctx_parent', {}))
        ctx.update(**env.ctx.get(self.get_name(), {}))
        ctx.update(**kwargs.get('ctx', {}))
        for k,v in env.iteritems():
            if not hasattr(self, k):
                envcopy[k] = formatloc(v, ctx)
        context.update(**envcopy)

        # parent variables
        context.update(**kwargs.get('ctx_parent', {}))

        # Do not pass internal Soppa variables onward from parent
        for k in self.ignored_internal_variables:
            if context.get(k):
                del context[k]

        # global class variables
        context.update(**env.ctx.get(self.get_name(), {}))

        # instance variables
        context.update(**kwargs.get('ctx', {}))

        # set initial state based on context
        for k,v in context.iteritems():
            if not self.has_need(k):
                setattr(self, k, v)

    def is_performed(self, fn):
        env.performed.setdefault(env.host_string, {})
        env.performed[env.host_string].setdefault(fn, False)
        return env.performed[env.host_string][fn]

    def set_performed(self, fn):
        self.is_performed(fn)
        env.performed[env.host_string][fn] = True

    def parent_context(self):
        """ Context to pass onto dependencies """
        c = {
            'project': self.project,
        }
        return c

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
        if env.local_deployment:
            return self.local_sudo(command, *args, **kwargs)
        return fabric_sudo(self.fmt(command), *args, **kwargs)

    def run(self, command, **kwargs):
        if env.local_deployment:
            return self.local(command, **kwargs)
        if kwargs.get('use_sudo'):
            return self.sudo(command, **kwargs)
        else:
            return fabric_run(self.fmt(command), **kwargs)

    def local(self, command, capture=False, shell=None):
        return fabric_local(self.fmt(command), capture=capture, shell=shell)

    def put(self, local_path, remote_path, **kwargs):
        local_path = getattr(local_path, 'name', local_path)
        if env.local_deployment:
            return self.local_put(self.fmt(local_path), self.fmt(remote_path), **kwargs)
        if env.get('use_sudo'):
            kwargs['use_sudo'] = True
        return fabric_put(self.fmt(local_path), self.fmt(remote_path), **kwargs)

    # NOTE: get collides with Python dictionaries
    def get_file(self, remote_path, local_path, **kwargs):
        local_path = getattr(local_path, 'name', local_path)
        if env.local_deployment:
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
        return any([string == k.split('.')[-1] for k in self.get_needs(as_str=True)])

    def find_need(self, string):
        for k in self.get_needs(as_str=True):
            if re.findall(string, k):
                return k
        return None

    def package_configuration(self, recipe):
        """ Copy default configuration under current project, and download cached copies """
        for k,v in recipe.packages.iteritems():
            print "Installing recipe packages",recipe,v
            source = here(instance=recipe)
            rpath = os.path.join(source, v)
            if k=='pip':
                self.pip.prepare_python_packages(rpath)
            elif k=='pip.venv':
                self.pip.prepare_python_packages(rpath)
            elif k=='apt':
                if isinstance(v, basestring):
                    v = [v]
                if not env.TESTING:
                    if self.operating.is_linux():
                        self.apt.update()
                        self.apt.install(v)
            else:
                raise Exception("Unknown configuration format")

    def package_configuration_install(self, recipe):
        pass

    def install_all_packages(self):
        self.package_configuration(self)
        for recipe in self.get_needs():
            self.package_configuration(recipe)
        if not self.TESTING:
            self.pip.synchronize_python_packages()

    def add_need(self, string):
        if self.find_need(string):
            return
        self.needs.append(string)
        self.get_and_load_need(string)

    def fmt(self, string, **kwargs):
        """ Format a string.
        self.fmt(string) vs string.format(**self.get_ctx())
        self.fmt(string, foo=2) vs string.format(foo=2, **self.get_ctx())
        """
        ctx = self.get_ctx(**kwargs)
        result = formatloc(string, ctx)
        possible_unfilled_vars = ('{' in result)
        if possible_unfilled_vars:
            env.possible_bugged_strings.append([string,result])
        return result

    def up(self, frm, to, ctx={}):
        """ Upload a template, with arguments relative to calling path """
        caller_path = here(fn=inspect.getfile(sys._getframe(1)))
        upload = Upload(frm, to, instance=self, caller_path=caller_path)
        self.template.up(*upload.args, context=self.get_ctx(**ctx))

    def copy_configuration(self, recurse=False):
        """ Prepare local copies of module configuration files. Does not overwrite existing files. """
        if os.path.exists(self.module_conf_path()):
            self.local('mkdir -p {0}'.format(self.local_module_conf_path()))
            with settings(warn_only=True):
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
        return os.path.join(self.module_path(), self.local_conf_path, '')

    def local_module_conf_path(self):
        return os.path.join(
            env.local_project_root,
            self.local_conf_path,
            self.get_name(),
            '')

    def setup(self):
        return {}

    def configure(self):
        return {}

    def get_name(self):
        return self.__class__.__name__.lower()

    def get_class_settings(self, for_self=False):
        """ Get all class and instance variables.
        - __dict__ is not enough.
        - namespace module keys, to be usable directly, or via module instance (foo_bar vs foo.bar)
        """
        rs = {}
        def is_valid(key, value):
            # TODO: only allow strings, numbers?
            if not key.startswith('__')\
                and not inspect.ismethod(value)\
                and not inspect.isfunction(value)\
                and not inspect.isclass(value):
                return True
            return False
        def is_for_module(key):
            if key \
                    and not for_self \
                    and key not in self.reserved_keys \
                    and key in module_keys:
                        return True
            return False
        values = inspect.getmembers(self)
        module_keys = self.__class__.__dict__.keys()
        for key,value in values:
            if is_valid(key, value):
                if is_for_module(key):
                    namespaced_key = key
                    if not key.startswith('{0}_'.format(self.get_name())):
                        namespaced_key = '{0}_{1}'.format(self.get_name(), key)
                    rs[namespaced_key] = value # module scope
                else:
                    rs[key] = value # global scope
        return rs

    def get_ctx(self, **kwargs):
        """ Gather and evaluate variables for context """
        rs = LocalDict()
        needs = self.get_needs()
        for k,v in enumerate(needs):
            rs.update(**v.get_class_settings())
        rs.update(**self.get_class_settings(for_self=False))
        rs.update(**self.get_class_settings(for_self=True))
        rs.update(**kwargs)
        for k,v in rs.iteritems():
            rs[k] = formatloc(v, rs)
        return rs
    
    def get_needs(self, as_str=False):
        """ Return module dependendies defined in needs=[] and need_* """
        key = 'get_needs.{0}'.format(as_str)
        if not self._CACHE.get(key):
            rs = set()
            for k in self.needs:
                name = k.split('.')[-1]
                if as_str:
                    rs.add(k)
                else:
                    rs.add(getattr(self, name))

            for k,v in self.get_class_settings(for_self=True).iteritems():
                if k.startswith('need_'):
                    name = v.split('.')[-1]
                    if as_str:
                        rs.add(v)
                    else:
                        rs.add(getattr(self, name))
            self._CACHE[key] = list(rs)
        return self._CACHE[key]

    def get_package_handler(self, name):
        return import_string(self.package_handlers[name])

    def get_packages(self):
        rs = {k:[] for k in self.packages.keys()}
        for need in [self] + self.get_needs():
            for name,path in need.packages.iteritems():
                handler = self.get_package_handler(name)(need=need)
                packages = handler.read(path)
                if packages:
                    rs[name].append({need: packages})
        return rs

    def finalize_packages(self, packages):
        rs = {k:[] for k in self.packages.keys()}
        for handler_name, load in packages.iteritems():
            for need, pkg in load[0].iteritems():
                handler = self.get_package_handler(handler_name)(need=need)
                existing_package_names = [handler.requirementName(k) for k in rs[handler_name]]
                for package in pkg:
                    if handler.requirementName(package) not in existing_package_names:
                        rs[handler_name].append(package)
        return rs

    def write_final_packages(self, packages):
        for handler_name, pkg in packages.iteritems():
            filepath = os.path.join(self.local_conf_path,
                    self.get_name(),
                    self.packages[handler_name])
            if not os.path.exists(filepath):
                with open(filepath, "w+") as f:
                    f.write("\n".join(pkg))


    def settings(self):
        return {}

    def cli_interface(self, action=None, *args, **kwargs):
        raise Exception("TODO")

    def get_and_load_need(self, key, *args, **kwargs):
        """ On-demand needs=[] resolve """
        # remove instance specific kwargs.ctx
        name = key.split('.')[-1]
        module = import_string(key)
        fn = getattr(module, name)

        instance = fn(ctx_parent=self.parent_context())
        setattr(self, name, instance)

        return instance

    def __getattr__(self, key):
        try:
            return self.__dict__[key]
        except Exception, e:
            # lazy-load dependencies
            if not key.startswith('__') and self.has_need(key):
                return self.get_and_load_need(self.find_need(key),
                        *self.args,
                        **self.kwargs)
            raise

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


class Runner(object):
    def __init__(self, state={}):
        self.state = state

    def ask_sudo_password(self, capture=False):
        if env.get('password') is None:
            print "SUDO PASSWORD PROMPT (leave blank, if none needed)"
            env.password = getpass.getpass('Sudo password ({0}):'.format(env.host))

    def setup(self, module):
        self.ask_sudo_password(capture=False)

        needs = module.get_needs()

        self.configure(needs)

        module.setup()

        self.restart(needs)

    def configure(self, needs):
        print "Configuring"
        pip_packages = set()
        newProject = False
        if not os.path.exists(self.local_config_path):
            newProject = True

        for need in needs:
            print "Gathering configuration for:",need.get_name()
            need.configure()

            need.copy_configuration()

        if newProject:
            raise Exception('Default Configuration generated into config/. Review settings. Next run is live')

        #self.pip.update_packages(packages=list(pip_packages))
        for need in needs:
            """
            if need.has_need('pip'):
                need.pip.packages_as_local()
                need.pip.install_package_global(self.version)
            """

    def restart(self, needs):
        print "Restarting"
        for need in needs:
            if hasattr(need, 'restart'):
                print "Restarting:",need.get_name()
                need.restart()
