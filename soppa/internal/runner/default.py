import os, copy, time
from pprint import pprint as pp
import itertools

from fabric.api import env, execute, task

from soppa.internal.mixins import NeedMixin, ApiMixin, FormatMixin, ReleaseMixin
from soppa.internal.tools import import_string, generate_config
from soppa.internal.logs import dlog

class RunnerReleaseMixin(ApiMixin, FormatMixin, NeedMixin):
    needs = ['soppa.operating',]

    @property
    def release_path(self):
        if not hasattr(self, 'time'):
            self.time = time.strftime('%Y%m%d%H%M%S')
        return self.fmt('{basepath}releases/{time}/')

    def ownership(self, owner=None):
        owner = owner or self.deploy_user
        self.sudo('chown -fR {owner} {basepath}', owner=owner)

    def dirs(self):
        self.sudo('mkdir -p {www_root}dist/')
        self.sudo('mkdir -p {basepath}{packages,releases/default/,media,static,dist,logs,config/vassals/,pids,cdn}')
        self.run('mkdir -p {}'.format(self.release_path))
        if not self.exists(self.path):
            with self.cd(self.basepath):
                self.run('ln -s {basepath}releases/default www.new; mv -T www.new www')

    def symlink(self):
        """ mv is atomic op on unix; allows seamless deploy """
        with self.cd(self.basepath):
            if self.operating.is_linux():
                self.run('ln -s {} www.new; mv -T www.new www'.format(self.release_path.rstrip('/')))
            else:
                self.run('rm -f www && ln -sf {} www'.format(self.release_path.rstrip('/')))

    def copy_path_files_to_release_path(self):
        # files uploaded to {path} will be lost on symlink; copy prior to that over to {release_path}
        for name,data in dlog.data['hosts'][env.host_string].iteritems():
            for key in data.keys():
                for k, action in enumerate(data[key]):
                    target = action.get('target')
                    if target:
                        if self.path in target:
                            release_target = target.replace(self.path, self.release_path)
                            self.run('cp {} {}'.format(target, release_target))

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

class Runner(NeedMixin):
    """
    A Runner allows more control over deployments, by acting as a wrapper around the deployment life-cycle.
    """
    needs = ['soppa.operating',
            'soppa.remote',
            'soppa.git',]
    release_cls = RunnerReleaseMixin
    def __init__(self, config={}, hosts={}, roles={}, recipe={}, *args, **kwargs):
        super(Runner, self).__init__(*args, **kwargs)
        self.config = config
        if not self.config.get('defer_handlers'):
            self.config['defer_handlers'] = '*'
        self.hosts = hosts
        self.roles = roles
        self.recipe = recipe
        self._CACHE = {}

    _modules = None
    def get_module_classes(self):
        if not self._modules:
            modules = []
            for m in self.current_recipe.get('modules', []):
                module = import_string(m)
                name = m.split('.')[-1]
                fn = getattr(module, name)
                modules.append(fn)
            self._modules = modules
        return self._modules

    def get_release(self, module):
        key = 'release_{}'.format(module.get_name())
        data = self._CACHE.get(key)
        if not data:
            data = self.release_cls()
            config = self.get_module_config(module)
            for k,v in config.iteritems():
                setattr(data, k, v)
            self._CACHE[key] = data
        return data

    def get_module_config(self, module):
        key = 'module_config_{}'.format(module.get_name())
        data = self._CACHE.get(key)
        if not data:
            data = generate_config(module, include_cls=[ReleaseMixin])
            self._CACHE[key] = data
        return data
    
    def get_module(self):
        return self.get_modules()[0]

    def get_roles_for_host(self, name):
        roles = []
        for k,v in self.roles.iteritems():
            if name in v.get('hosts', []):
                roles.append(k)
        return roles

    def get_hosts_for(self, name):
        """ resolve roles to hosts """
        def as_list(data):
            if isinstance(data, basestring):
                data = [data]
            return list(data)
        all_hosts = list(set(itertools.chain.from_iterable([as_list(v['hosts']) for k,v in self.roles.iteritems()])))
        if name in ['*', 'all']:
            return list(all_hosts)
        if self.roles.get(name):
            return as_list(self.roles[name].get('hosts', []))
        return name

    def run(self):
        """ A run lives in a Fabric execution (env.host_string) context """
        print "RUN: {}".format(self)
        if not all([self.get_hosts_for(ingredient['roles']) for ingredient in self.recipe]):
            raise Exception("No hosts configured for {}".format(ingredient))

        for ingredient in self.recipe:
            hosts = self.get_hosts_for(ingredient['roles'])
            modules = ingredient['modules']
            # create a new standalone instance for execution
            runner = Runner(
                    config=self.config,
                    hosts=self.hosts,
                    roles=self.roles,
                    recipe=self.recipe)
            runner.current_recipe = ingredient
            execute(runner._run, hosts=hosts)

    def _run(self, ingredient={}):
        """ At this point in time execution is on a specific host. Configuration prepared accordingly """
        print "host_string: {}, recipe: {}".format(env.host_string, self.current_recipe)
        config = copy.deepcopy(self.config)
        # Configuration: hosts > roles > config > classes
        role_config = {}
        for role in self.get_roles_for_host(env.host_string):
            role_config.update(self.roles[role].get('config', {}))
        config.update(role_config)
        config.update(self.hosts.get(env.host_string, {}))

        needs_all = set()
        module_classes = self.get_module_classes()

        # instantiate with configuration
        modules = []
        for module in module_classes:
            modules.append(module(config))

        if not modules:
            print "Nothing to do, exiting."
            return

        self.ask_sudo_password(modules[0], capture=False)
        
        # configure, prepare dependent modules
        for module in modules:
            release = self.get_release(module)

            needs = module.get_needs()
            for need in needs:
                needs_all.add(need)

            if release.project:
                release.dirs()
            release.ownership()

            # configure everything
            self.configure(needs)

            # setup everything, except self
            for need in needs:
                release.setup_need(need)

        # configure self (modules)
        for module in modules:
            self.configure([module])
            self.packages(module)

        # setup self (modules)
        for module in modules:
            module.setup()

        # symlink self (modules)
        for module in modules:
            release = self.get_release(module)
            release.copy_path_files_to_release_path()
            release.symlink()

        self.restart(needs_all)

    def configure(self, needs):
        """ Prepare pre-requisitives a module has, before it can be setup """
        newProject = False
        for need in needs:
            if not os.path.exists(os.path.join(need.soppa.local_conf_path)):
                newProject = True
            need.configure()
            need.copy_configuration()

        if newProject:
            raise Exception("""NOTICE: Default Configuration generated into {}.
            Review settings and configure any changes. Next run is live""".format('$local_conf_path'))

    def packages(self, module):
        """ Package handling bundled between all modules, executed once per server.
        - Runner needs packages instances
        """
        pm = module.packman()
        packages = pm.get_packages()
        pm.write_packages(packages)
        pm.download_packages(packages)
        pm.sync_packages(packages)
        pm.install_packages(packages)

    def ask_sudo_password(self, module, capture=False):
        if module.env.get('password') is None:
            print "SUDO PASSWORD PROMPT (leave blank, if none needed)"
            module.env.password = getpass.getpass('Sudo password ({0}):'.format(env.host))

    def restart(self, needs):
        for k,v in dlog.data['hosts'][env.host_string].iteritems():
            if k == 'all':
                for deferred in v.get('defer'):
                    if deferred['modified']:
                        deferred['instance']()
                        #instance.restart()
