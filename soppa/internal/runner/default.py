import os
from soppa.internal.mixins import DeployMixin, NeedMixin

class Runner(DeployMixin, NeedMixin):
    """ A Runner allows more control over deployments by centralizing things like eg. service restarts """
    needs = ['soppa.operating',
            'soppa.remote',
            'soppa.git',]
    def __init__(self, state={}, *args, **kwargs):
        super(Runner, self).__init__(*args, **kwargs)
        self.state = state
        self.module = None
        self._roles = {}

    def roles(self, role, tasks):
        self._roles[role] = tasks

    def setup(self, module):
        self.module = module
        self.ask_sudo_password(capture=False)

        # 0% gather needs of all installable modules
        needs = module.get_needs()

        if self.module.project:
            self.module.dirs()
        self.module.ownership()

        # configure everything
        self.configure(needs + [module])

        # setup everything, except self
        for need in needs:
            need.setup_needs()#need.setup()

        # setup self
        module.go()

        self.restart(needs)

    def configure(self, needs):
        """ Prepare pre-requisitives a module has, before it can be setup """
        newProject = False
        if not os.path.exists(os.path.join(self.module.soppa.local_conf_path)):
            newProject = True

        for need in needs:
            need.configure()
            need.copy_configuration()

        if newProject:
            raise Exception("""NOTICE: Default Configuration generated into {}.
            Review settings and configure any changes. Next run is live""".format(self.module.soppa.local_conf_path))

        # Runner needs packages instances
        packages = self.module.packman().get_packages()
        self.module.packman().write_packages(packages)
        self.module.packman().download_packages(packages)
        self.module.packman().sync_packages(packages)
        self.module.packman().install_packages(packages)

    def fmt(self, val, *args, **kwargs):#TODO: belongs elsewhere
        return self.module.fmt(val)

    def ask_sudo_password(self, capture=False):
        if self.module.env.get('password') is None:
            print "SUDO PASSWORD PROMPT (leave blank, if none needed)"
            self.module.env.password = getpass.getpass('Sudo password ({0}):'.format(env.host))

    def restart(self, needs):
        for need in needs:
            if hasattr(need, 'restart'):
                if need.isDirty():
                    print "Restarting:",need.get_name()
                    need.restart()
