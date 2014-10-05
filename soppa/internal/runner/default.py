import os, copy, time, getpass
from pprint import pprint as pp
import itertools

from fabric.api import env, execute, task

from soppa.internal.mixins import NeedMixin, ApiMixin, FormatMixin, ReleaseMixin
from soppa.internal.tools import import_string, generate_config
from soppa.internal.config import update_config, Config, load
from soppa.internal.local import local_deploy


class Runner(NeedMixin):
    """
    A Runner allows more control over deployments, by acting as a wrapper around the deployment life-cycle.
    """
    def __init__(self, config={}, hosts={}, roles={}, recipe={}, *args, **kwargs):
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
                modules.append(NeedMixin().load(m))
            self._modules = modules
        return self._modules

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
        if not all([self.get_hosts_for(ingredient['roles']) for ingredient in self.recipe]):
            raise Exception("No hosts configured for {}".format(ingredient))

        for ingredient in self.recipe:
            hosts = self.get_hosts_for(ingredient['roles'])
            modules = ingredient['modules']
            if self.config.get('local_deployment', False):
                local_config = local_deploy()
                self.config.update(local_config)
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

        module_classes = self.get_module_classes()

        # generate default .ini
        # A single deployment is a shared entity, as in, the configuration encompasses everything (thus module_classes[0] for config)
        DEFAULT_INI_NAME = 'config.ini'
        config_path = '{}{}'.format(module_classes[0]().soppa.local_conf_path, DEFAULT_INI_NAME)
        # TODO: load any configuration files, or if none specified, use default configuration
        # default configuration
        all_instances, values = update_config(module_classes[0], path=None, ctx=config)

        # flatten {namespace}_key=>val, to be picked up correctly within modules
        flatval = {}
        for k,v in values.get('globals', {}).iteritems():
            flatval.setdefault(k, v)
        values.pop('globals', False)
        for k,v in values.iteritems():
            if isinstance(v, dict):
                for k2,v2 in v.iteritems():
                    key = k2
                    if not key.startswith(k):
                        key = '{}_{}'.format(k, k2)
                    flatval.setdefault(key, v2)
        # TODO: load only config-files specified in deployment-recipe
        flatval.update(config)
        config = flatval

        # instantiate with configuration
        modules = []
        instances = []
        for module in module_classes:
            modules.append(module(config))
        # update_config instances do not have the whole configuration spectrum; re-initialize
        for instance in all_instances:
            instances.append(getattr(modules[0], instance.get_name()))

        if not modules:
            print "Nothing to do, exiting."
            return

        # remove parent module from child instance list
        r = []
        for k,instance in enumerate(instances):
            if instance.get_name() == modules[0].get_name():
                r.append(k)
        for k in r:
            instances.pop(k)

        # copy configuration
        isnew = []
        cfg = {}
        isnew.append(self.configure(instances))
        for module in modules:
            isnew.append(self.configure([module]))
            cfg.update(generate_config(module))

        if any(isnew):
            raise Exception("""NOTICE: Default Configuration generated into {}.
            Review settings and configure any changes. Next run is live""".format('$local_conf_path'))
        
        for module in modules:
            if hasattr(module, 'pre_setup'):
                module.pre_setup()

        # child dependencies: packaging
        for module in modules:
            for instance in instances:
                # default settings
                # NOTE: packages() returns instances spawned from caller
                child = getattr(module, instance.get_name())
                packages = child.packages()
                child.packages_getset(packages)

                # project settings
                child = getattr(module, instance.get_name())
                path = os.path.join(child.soppa.abs_conf_path, child.get_name(), '')
                packages = child.packages(path=path)
                child.packages_getset(packages)
            # parent dependencies: packaging
            packages = module.packages()
            module.packages_getset(packages)

        # child dependencies: setup
        for module in modules:
            for instance in instances:
                instance.setup()

        # parent: setup
        for module in modules:
            module.setup()

        # run deferred handlers
        self.restart(modules)

    def configure(self, needs):
        """ Prepare pre-requisitives a module has, before it can be setup """
        newProject = False
        for need in needs:
            if not os.path.exists(os.path.join(need.soppa.local_conf_path)):
                newProject = True
            need.copy_configuration()
        return newProject

    def ask_sudo_password(self, module, capture=False):
        if module.env.get('password') is None:
            print "SUDO PASSWORD PROMPT (leave blank, if none needed)"
            module.env.password = getpass.getpass('Sudo password ({0}):'.format(env.host))

    def restart(self, modules):
        deferred = []
        # TODO: group, could be multiple changed files per module
        for module in modules:
            if not module.log.data['hosts'].get(env.host_string):
                continue
            for k,v in module.log.data['hosts'][env.host_string].iteritems():
                if k == 'all':
                    deferred.append(v)
        for k in deferred:
            for deferred in k.get('defer'):
                if deferred['modified']:
                    deferred['instance']()
