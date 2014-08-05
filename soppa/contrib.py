import os, sys, copy, re, datetime
from contextlib import contextmanager
import inspect, getpass, zlib
from functools import wraps
from optparse import OptionParser
from subprocess import call

# import and prefix fabric functions into their own namespace to not inadvertedly use them
from fabric.api import cd as fabric_cd, local as fabric_local, run as fabric_run, sudo as fabric_sudo, task as fabric_task, put as fabric_put, execute as fabric_execute, hide as fabric_hide, lcd as fabric_lcd, get as fabric_get, put as fabric_put
from fabric.contrib.files import exists as fabric_exists
from fabric.context_managers import prefix as fabric_prefix, settings
from fabric.decorators import with_settings
from fabric.operations import prompt as fabric_prompt

from soppa import *
from soppa.fmt import fmtkeys, formatloc, escape_bad_matches
from soppa.tools import import_string, Upload

env.possible_bugged_strings = []

def get_methods(klass):
    return [k[0] for k in inspect.getmembers(klass, predicate=inspect.ismethod)]

class PackageManager(object):
    def __init__(self, instance):
        self.instance = instance
        self._CACHE = {}
        self.handlers = []
        self.storages = ['package','meta']#TODO: belongs in handler?

        for need in [self.instance] + self.instance.get_needs():
            for name in self.instance.env.packmans:
                handin = import_string(name)(need=need)
                self.handlers.append(handin)

    def unique_handlers(self):
        key = 'unique_handlers'
        if not self._CACHE.get(key):
            self._CACHE[key] = [import_string(name)(need=self.instance) for name in self.instance.env.packmans]
        return self._CACHE[key]
            
    def get_packages(self):
        """ Flatten packages into a single source of truth, ensuring needs do not override existing project dependencies """
        rs = {k:{'meta':[], 'package':[]} for k in self.unique_handlers()}
        def handler_group(handler):
            for uh in self.unique_handlers():
                if handler.__class__.__name__ == uh.__class__.__name__:
                    return uh
            raise Exception('Unknown handler')

        for handler in self.handlers:
            handler.read()
            for storage in self.storages:
                for package in getattr(handler, storage).all():
                    existing_package_names = [handler.requirementName(k) for k in rs[handler_group(handler)][storage]]
                    if handler.requirementName(package) not in existing_package_names:
                        rs[handler_group(handler)][storage].append(package)
        return rs

    def write_packages(self, packages):
        """ One project, single requirement files (encompasses all dependencies).
        To install everything need multiple installs.
        Does not overwrite existing settings.
        """
        for handler, pkg in packages.iteritems():
            filepath = handler.target_need_conf_path()
            if not os.path.exists(os.path.dirname(filepath)):
                self.instance.local('mkdir -p {0}'.format(os.path.dirname(filepath)))#TODO: elsewhere; Dir.ensure_exists(path)
            if not os.path.exists(filepath):
                handler.write(filepath, pkg)

    def sync_packages(self, packages):
        for handler, pkg in packages.iteritems():
            filepath = handler.target_need_conf_path()
            handler.get_need().sync()

    def download_packages(self, packages):
        """ Download local copies of packages """
        for handler, pkg in packages.iteritems():
            filepath = handler.target_need_conf_path()
            handler.get_need().download(filepath, new_only=True)

    def install_packages(self, packages):
        for handler, pkg in packages.iteritems():
            if pkg['package']:
                handler.install(pkg['package'])

class NoOp(object):
    succeeded = True
    failed = False
    def __enter__(self):
        pass
    def __exit__(self, type, value, traceback):
        pass
    def __iter__(self):
        return self
    def next(self):
        raise StopIteration
    def __unicode__(self):
        return ""

class MetaClass(type):
    """ Monitor API methods. Used to implement dry-run, logging """
    @staticmethod
    def wrapper(fun):
        @wraps(fun)
        def _(self, *args, **kwargs):
            dry_run = os.environ.get('DRYRUN', False)
            if dry_run:
                result = NoOp()
                print '[{0}]'.format(env.host_string), '{0}.{1}:'.format(self.get_name(), fun.__name__), args,kwargs
            else:
                result = fun(self, *args, **kwargs)
            return result
        return _

    def __new__(cls, name, bases, attrs):
        for aname,fun in attrs.iteritems():
            if callable(fun):
                if aname.startswith('_'):
                    continue
                if aname in API_METHODS:
                    attrs[aname] = cls.wrapper(attrs[aname])
        return super(MetaClass, cls).__new__(cls, name, bases, attrs)

# get_methods(ApiMixin)
API_METHODS = ['cd', 'exists', 'get_file', 'hide', 'local', 'local_get', 'local_put', 'local_sudo', 'mlcd', 'prefix', 'put', 'run', 'sudo', 'up']

class ApiMixin(object):
    __metaclass__ = MetaClass
    """ Methods with side-effects """
    sudo_expect = ['shell', 'group', 'stderr', 'stdout', 'quiet', 'user', 'timeout', 'warn_only', 'shell_escape', 'pty', 'combine_stderr']
    run_expect = ['shell', 'shell_escape', 'stderr', 'stdout', 'quiet', 'timeout', 'warn_only', 'pty', 'combine_stderr']
    # Fabric API
    def hide(self, *groups):
        return fabric_hide(*groups)

    def _expects(self, data, supported):
        return {k:v for k,v in data.iteritems() if k in supported}

    def sudo(self, command, **kwargs):
        if env.local_deployment:
            return self.local_sudo(command, **kwargs)
        return fabric_sudo(self.fmt(command, **kwargs), **self._expects(kwargs, self.sudo_expect))

    def run(self, command, **kwargs):
        if env.local_deployment:
            return self.local(command, **kwargs)
        if kwargs.get('use_sudo'):
            return self.sudo(command, **kwargs)
        else:
            return fabric_run(self.fmt(command, **kwargs), **self._expects(kwargs, self.run_expect))

    def local(self, command, capture=False, shell=None):
        return fabric_local(self.fmt(command), capture=capture, shell=shell)

    def put(self, local_path, remote_path, **kwargs):
        local_path = getattr(local_path, 'name', local_path)
        if env.local_deployment:
            return self.local_put(self.fmt(local_path), self.fmt(remote_path), **kwargs)
        if env.get('use_sudo'):
            kwargs['use_sudo'] = True
        return fabric_put(self.fmt(local_path), self.fmt(remote_path), **kwargs)

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

    @contextmanager
    def mlcd(self, path):
        """ Really move to a (relative) local directory, unlike lcd """
        calling_file = inspect.getfile(sys._getframe(2))
        d = here(path, fn=calling_file)
        try:
            yield os.chdir(d)
        finally:
            os.chdir(env.basedir)

    def up(self, frm, to=None, ctx={}):
        """ Upload a template, with arguments relative to calling path """
        caller_path = here(instance=self)
        to = to or self.conf_dir
        #TODO:inspecting frames and wrappers do not seem to play well together
        #caller_path = here(fn=inspect.getfile(sys._getframe(1)))
        upload = Upload(frm, to, instance=self.parent(), caller_path=caller_path)
        self.template.up(*upload.args, context=self.parent())

class DeployMixin(ApiMixin):
    def setup_needs(self):
        for instance in self.get_needs():
            key_name = '{0}.setup'.format(instance.get_name())
            if self.is_performed(key_name):
                continue
            getattr(instance, 'setup')()
            self.set_performed(key_name)

    def ownership(self, owner='root'):
        self.sudo('chown -fR {owner} {release.basepath}'.format(owner=owner))

    def dirs(self):
        self.sudo('mkdir -p {www_root}dist/')
        self.sudo('mkdir -p {basepath}{packages,releases/default/,media,static,dist,logs,config/vassals/,pids,cdn}')
        self.run('mkdir -p {release_path}')
        if not self.exists('{basepath}www/'):
            with self.cd('{basepath}'):
                self.run('ln -s {releases}default/ www.new; mv -T www.new www')

class InspectMixin(object):

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

class NeedMixin(InspectMixin):
    project = None
    needs = []
    def __init__(self, *args, **kwargs):
        self._CACHE = {}
        self.args = args
        self.kwargs = kwargs
    
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

    def find_need(self, string):
        for k in self.get_needs(as_str=True):
            if re.findall(string, k):
                return k
        return None

    def add_need(self, string):
        if self.find_need(string):
            return
        self.needs.append(string)
        self.get_and_load_need(string)

    def has_need(self, string):
        return any([string == k.split('.')[-1] for k in self.get_needs(as_str=True)])

    def get_and_load_need(self, key, *args, **kwargs):
        """ On-demand needs=[] resolve """
        name = key.split('.')[-1]
        module = import_string(key)
        fn = getattr(module, name)

        instance = fn(ctx_parent=self.parent_context())
        setattr(self, name, instance)

        return instance

    def parent_context(self):
        """ Context passed for dependant needs """
        return {
            'parent_instance': self,
        }

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

class DeployLog(object):
    def __init__(self, *args, **kwargs):
        self.data = {}
        meta = {
            'user': os.environ.get('USER', env.user),
            'date': datetime.datetime.now().isoformat(),
            'machine': os.popen('uname -a').read().strip(),}
        self.data['meta'] = meta
        self.data['hosts'] = {}

    def add(self, bucket, need, data):
        host = env.host_string
        need_name = need.get_name()
        hosts = self.data['hosts']
        hosts.setdefault(host, {})
        hosts[host].setdefault(need_name, {})
        hosts[host][need_name].setdefault(bucket, [])
        hosts[host][need_name][bucket].append(data)
dlog = DeployLog()

class Soppa(DeployMixin, NeedMixin):
    reserved_keys = ['needs','reserved_keys']
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

        # fabric environment
        self.env = env

        # Configuration
        context = {}

        # parent variables
        context.update(**kwargs.get('ctx_parent', {}))

        # global class variables
        context.update(**env.ctx.get(self.get_name(), {}))

        # instance variables
        context.update(**kwargs.get('ctx', {}))

        if any([key in self.reserved_keys for key in context.keys()]):
            raise Exception("Reserved keys used")

        # set initial state based on context
        for k,v in context.iteritems():
            if not self.has_need(k):
                setattr(self, k, v)

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

    def parent(self):
        # TODO: traverse until root parent?
        return self.parent_instance if hasattr(self, 'parent_instance') else self

    def fmt(self, string, **kwargs):
        """ Format a string.
        self.fmt(string) vs string.format(self=self)
        self.fmt(string, foo=2) vs string.format(foo=2, self=self)

        Add self as formatting argument
        {foo} => {self.foo}.format(self=self)
        {foo} kwargs(foo=2) => {foo}.format(foo=foo)
        {foo.bar} kwargs(foo=2) => {foo}.format(self=self)
        """
        for times in range(6):
            if isinstance(string, basestring):
                string = escape_bad_matches(string)
                if '{' not in string:
                    break
            keys = fmtkeys(string)
            kwargs_keys = kwargs.keys()
            add_self = False
            if all([key not in kwargs_keys for key in keys]):
                add_self = True
            for key in kwargs_keys:
                if '.' in key:
                    add_self = True
            if add_self:
                kwargs['self'] = self
            for key in keys:
                if key not in kwargs_keys:
                    if not key.startswith('self.'):
                        string = string.replace('{'+key+'}', '{self.'+key+'}')
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


class Runner(DeployMixin, NeedMixin):
    needs = ['soppa.operating','soppa.remote']
    def __init__(self, state={}, *args, **kwargs):
        super(Runner, self).__init__(*args, **kwargs)
        self.state = state
        self.module = None

    def setup(self, module):
        self.module = module
        self.ask_sudo_password(capture=False)

        if env.project:
            self.dirs()
        self.ownership()

        needs = module.get_needs()
        self.configure([module] + needs)

        self.tar_from_git()
        self.upload_tar()

        module.go()
        module.remote.setup_runner()
        #self.remote.setup_runner() -- remote assumes Soppa-inheritance

        self.ownership()
        self.symlink_release()

        self.restart(needs)

    def configure(self, needs):
        newProject = False
        if not os.path.exists(os.path.join(env.local_conf_path)):
            newProject = True

        for need in needs:
            need.configure()
            need.copy_configuration()
            need.setup_needs()

        if newProject:
            raise Exception("""NOTICE: Default Configuration generated into {0}.
            Review settings and configure any changes. Next run is live""".format(env.local_conf_path))

        # Runner needs packages instances
        packages = self.module.packman().get_packages()
        self.module.packman().write_packages(packages)
        self.module.packman().download_packages(packages)
        self.module.packman().sync_packages(packages)
        self.module.packman().install_packages(packages)

    def fmt(self, val, *args, **kwargs):#TODO: belongs elsewhere
        return self.module.fmt(val)

    def ask_sudo_password(self, capture=False):
        if env.get('password') is None:
            print "SUDO PASSWORD PROMPT (leave blank, if none needed)"
            env.password = getpass.getpass('Sudo password ({0}):'.format(env.host))

    def restart(self, needs):
        for need in needs:
            if hasattr(need, 'restart'):
                if need.isDirty():
                    print "Restarting:",need.get_name()
                    need.restart()
