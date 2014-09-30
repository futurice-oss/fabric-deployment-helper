from contextlib import contextmanager
from functools import wraps
import os, sys, re, inspect, hashlib
import string, copy
from soppa.internal.tools import import_string, Upload, get_full_dict, get_namespaced_class_values, fmt_namespaced_values
from soppa import *

# FABRIC: import and prefix fabric functions into their own namespace to not inadvertedly use them
from fabric.api import cd as fabric_cd, local as fabric_local, run as fabric_run, sudo as fabric_sudo, task as fabric_task, put as fabric_put, execute as fabric_execute, hide as fabric_hide, lcd as fabric_lcd, get as fabric_get, put as fabric_put
from fabric.contrib.files import exists as fabric_exists
from fabric.context_managers import prefix as fabric_prefix, settings
from fabric.decorators import with_settings
from fabric.operations import prompt as fabric_prompt
# /FABRIC

def get_methods(klass):
    return [k[0] for k in inspect.getmembers(klass, predicate=inspect.ismethod)]

class MetaClass(type):
    """ Monitor API methods. Used to implement dry-run, logging """
    @staticmethod
    def wrapper(fun):
        @wraps(fun)
        def _(self, *args, **kwargs):
            def run_fn_behaviour(state, fn_name):
                metname = '{}_{}'.format(state, fn_name)
                if metname.endswith(fn_name) and hasattr(self, metname):
                    todoTestingPass=1
                    return getattr(self, metname)()
                return False

            def is_api_method(name):
                if name in API_METHODS:
                    return True
                return False

            dry_run = os.environ.get('DRYRUN', False)

            run_fn_behaviour('pre', fun.__name__)

            if dry_run and is_api_method(fun.__name__):
                result = NoOp()
                self.root.log.add_action([self, fun.__name__, args, kwargs])
            else:
                result = fun(self, *args, **kwargs)

            run_fn_behaviour('post', fun.__name__)

            return result
        return _

    def __new__(cls, name, bases, attrs):
        for aname,fun in attrs.iteritems():
            if callable(fun):
                if aname.startswith('_'):
                    continue
                if aname in META_METHODS:
                    attrs[aname] = cls.wrapper(attrs[aname])
        return super(MetaClass, cls).__new__(cls, name, bases, attrs)

# get_methods(ApiMixin)
API_METHODS = ['cd', 'exists', 'hide', 'local', 'prefix', 'put', 'run', 'sudo', 'get_file']
# get_file calls fabric_get
META_METHODS = API_METHODS+['setup','up','local_get','local_put','local_sudo','mlcd',]
# need_ALIAS: allows generalizing, so changing need_web = 'soppa.apache', all configs still work.

class ApiMixin(object):
    __metaclass__ = MetaClass
    """ Methods with side-effects """
    sudo_expect = ['shell', 'group', 'stderr', 'stdout', 'quiet', 'user', 'timeout', 'warn_only', 'shell_escape', 'pty', 'combine_stderr']
    run_expect = ['shell', 'shell_escape', 'stderr', 'stdout', 'quiet', 'timeout', 'warn_only', 'pty', 'combine_stderr']
    local_expect = ['capture', 'shell']
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
        if kwargs.get('user'):
            return self.sudo(command, **kwargs)
        else:
            return fabric_run(self.fmt(command, **kwargs), **self._expects(kwargs, self.run_expect))

    def local(self, command, **kwargs):
        return fabric_local(self.fmt(command, **kwargs), **self._expects(kwargs, self.local_expect))

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
            os.chdir(self.soppa.basedir)

    def up(self, frm, to=None, ctx={}):
        """ Upload a template, with arguments relative to calling path """
        caller_path = here(instance=self)
        if not to:
            raise Exception("Missing arguments")
        upload = Upload(frm, to, instance=self, caller_path=caller_path)
        return self.template.up(*upload.args, context=self.__dict__)

class ReleaseMixin(object):
    user = os.environ.get('USER', 'root')
    deploy_group = 'www-data'
    deploy_os = 'debian'
    project = None
    host = 'localhost'#TODO:for?

    www_root = '/srv/www/'
    packages_path = '{www_root}packages/'
    basepath = '{www_root}{project}/'
    path = '{basepath}www/'

    # defaults; TODO: rather, prompt for these on initial configuration?
    soppa_proc_daemon = 'supervisor'
    soppa_web_server = 'nginx'
    soppa_db_server = 'postgres'

    def get_default_modules(self):
        i = []
        if self.soppa_proc_daemon:
            i.append(getattr(self, self.soppa_proc_daemon))
        if self.soppa_web_server:
            i.append(getattr(self, self.soppa_web_server))
        return i

class NeedMixin(object):
    
    def get_needs(self, as_str=False):
        """ Return module dependendies defined in needs=[] and need_* """
        rs = set()
        if not hasattr(self, 'needs'):
            return []
        for k in self.needs:
            rs.add(k)
        rs = list(rs)
        if as_str:
            return rs
        return [getattr(self, name.split('.')[-1]) for name in rs]

    def find_need(self, string):
        for k in self.get_needs(as_str=True):
            if k.endswith(string):
                return k
        return string

    def has_need(self, string):
        for k in self.get_needs(as_str=True):
            k = k.split('.')[-1]
            if k.endswith(string):
                return True
        return False

    def rescope_namespaced_variables(self, curscope):
        """
        A(dict(a_b_c=1)) -- converts a_b_c => b_c, as it matches A
            a.b_c
        a = A(dict(b_c=1)) -- no changes
            a.b.b_c
            a.b.c
        """
        new_data = {}
        for k,v in curscope.iteritems(): # A.A_B_c => b_c
            if k.startswith('{}_'.format(self.get_name())):
                aliased_key = '_'.join(k.split('_')[1:])
                new_data[aliased_key] = v
        return new_data

    def load(self, name):
        """ Load a module class by its name
        nginx -> soppa.Nginx
        mymodule.nginx -> mymodule.Nginx
        """
        cls_name = name.split('.')[-1]
        import_name = copy.copy(name)
        if '.' not in name:
            module = None
            for ns in DEFAULT_NS:
                import_name = '{}.{}'.format(ns, name)
                try:
                    module = import_string(import_name)
                    break
                except Exception, e:
                    pass
        else:
            module = import_string(import_name)
        cls = self.match_module_to_class(module, cls_name)
        return getattr(module, cls)

    def match_module_to_class(self, module, name):
        pattern = '^{}$'.format(name.capitalize())
        matches = [re.findall(pattern, k, re.IGNORECASE) for k in module.__dict__.keys()]
        return [k.pop() for k in matches if k].pop()

    def get_and_load_need(self, key, alias=None, ctx={}):
        """ On-demand module resolve.
        self.nginx -> soppa.nginx -> Nginx()

        Pass configuration from parent.
        - own namespace
        - self.alias_var =>
            alias.var
            alias.alias_var
        To prevent recursion:
        - {alias.foo} => {foo}
        - {self.alias.foo} => {foo}
        - alias_key = '{key}' raises exception
        """
        name = key.split('.')[-1]
        cls = self.load(key)
        alias = alias or name

        curscope = {}
        curscope.update(**self.__dict__)
        def need_values(curscope, alias):
            cfg = {}
            for k,v in curscope.iteritems(): # A.B_c => b_c + c
                if k.startswith('{}_'.format(alias)):
                    v = curscope.get(k, v)# latest assigned value
                    keyname = k.split('{}_'.format(alias))[-1]
                    if isinstance(v, basestring):
                        v = v.replace('{{self.{}.'.format(alias), '{')
                        v = v.replace('{{{}.'.format(alias), '{')
                        if '{{{}}}'.format(keyname) in v:
                            raise Exception("Recursion detected: {}.{}={}".format(self, k, v))
                    cfg.setdefault(keyname, v)
                    cfg.setdefault(k, v)
            return cfg
        parent_values = {}
        for name in [alias]:
            parent_values.update(**need_values(curscope, name))

        context = {}
        context.update(**self.kwargs.get('ctx', {}))#parent configuration trickles down
        context.update(**parent_values)
        context['parent_instance'] = self

        return cls(ctx_parent=context)

    def _load_need(self, key, alias=None, ctx={}):
        return self.get_and_load_need(self.find_need(key), alias=alias, ctx=ctx)

    def is_installed_module(self, name):
        return name in [k.split('.')[-1] for k in self.soppa.installed_modules]

    def __getattr__(self, key):
        try:
            result = self.__dict__[key]
        except KeyError, e:
            # lazy-load modules
            if not key.startswith('__') and self.is_installed_module(key):
                instance = self._load_need(key, alias=None, ctx={'args':self.args, 'kwargs': self.kwargs})
                name = key.split('.')[-1]
                setattr(self, name, instance)
                # NoOp catches method calls only
                self.root.log.add_action([instance, '__init__', [], {}])
                return instance
            raise AttributeError(e)
        return result

class FormatMixin(object):
    ALLOWED_CHARS = string.ascii_letters + '_.'
    strict_fmt = True

    def is_ascii_letters(self, s, bucket):
        return all(c in bucket for c in s)

    def escape_bad_matches(self, s):
        for match in re.findall('{(.+?)}', s):
            if not self.is_ascii_letters(match, self.ALLOWED_CHARS):
                match = re.escape(match)
                s = re.sub('({0})'.format(match),
                        r'{\1}', s)
        return s

    def fmtkeys(self, s):
        return [k[1] for k in string.Formatter().parse(s) if k[1]]

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
                string = self.escape_bad_matches(string)
                if '{' not in string:
                    break
                keys = self.fmtkeys(string)
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
            try:
                string = string.format(**kwargs)
            except KeyError, e:
                if os.environ.get('DRYRUN', False):
                    string = 'dryrun'
                else:
                    raise
            except AttributeError, e:
                print 'FMT failed for: {} with {}'.format(string, kwargs)
                raise
        return string

class DirectoryMixin(object):
    """
    A deployment model for projects.
    Example:
    /www # www_root
    /www/project/ # basepath
    /www/project/www/ # path
    /www/project/releases/X/ # release_path
    www -> releases/X # <symlink>
    """

    def pre_setup(self):
        self.dirs()
        self.ownership()

    def post_setup(self):
        self.copy_path_files_to_release_path()
        self.symlink()

    @property
    def release_path(self):
        if not hasattr(self, 'time'):
            self.time = time.strftime('%Y%m%d%H%M%S')
        return self.fmt('{basepath}releases/{time}/')

    def ownership(self, owner=None):
        self.sudo('chown -fR {owner} {basepath}', owner=owner or self.user)

    def dirs(self):
        self.sudo('mkdir -p {www_root}dist/')
        self.sudo('mkdir -p {basepath}{packages,releases/default/,media,static,dist,logs,config/vassals/,pids,cdn}')
        self.sudo('mkdir -p {}'.format(self.release_path))
        if not self.exists(self.path):
            with self.cd(self.basepath):
                self.sudo('ln -s {basepath}releases/default www.new; mv -T www.new www')

    def symlink(self):
        """ mv is atomic op on unix; allows seamless deploy """
        with self.cd(self.basepath):
            if self.operating.is_linux():
                self.sudo('ln -s {} www.new; mv -T www.new www'.format(self.release_path.rstrip('/')))
            else:
                self.sudo('rm -f www && ln -sf {} www'.format(self.release_path.rstrip('/')))

    def copy_path_files_to_release_path(self):
        """
        Files uploaded to {path} will be lost on symlink; copy prior to that over to {release_path}
        """
        for name,data in self.log.data.get('hosts', {}).get(env.host_string, {}).iteritems():
            for key in data.keys():
                for k, action in enumerate(data[key]):
                    target = action.get('target')
                    if target:
                        if self.path in target:
                            release_target = target.replace(self.path, self.release_path)
                            reldir = os.path.dirname(release_target)
                            self.sudo('mkdir -p {}; cp {} {}'.format(reldir, target, release_target))

    def setup_need(self, instance):
        """ Ensures module.setup() is run only once per-host """
        key_name = '{0}.setup'.format(instance.get_name())
        if self.is_performed(key_name):
            return
        getattr(instance, 'setup')()
        self.set_performed(key_name)

    def is_performed(self, fn):
        env.performed.setdefault(env.host_string, {})
        env.performed[env.host_string].setdefault(fn, False)
        return env.performed[env.host_string][fn]

    def set_performed(self, fn):
        self.is_performed(fn)
        env.performed[env.host_string][fn] = True

    def id(self, url):
        return hashlib.md5(url).hexdigest()

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
    def __getitem__(self, index):
        return self
    def __setitem__(self, index, value):
        pass
    def __unicode__(self):
        return ""
