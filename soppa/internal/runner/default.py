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

    def setup(self, module):
        self.module = module
        self.ask_sudo_password(capture=False)

        needs = module.get_needs()

        if self.module.release.project:
            self.module.release.dirs()
        self.module.release.ownership()

        self.configure([module] + needs)

        #self.module.git.source()
        module.go()
        #module.remote.setup_runner()
        #self.module.release.ownership()
        #self.symlink_release()

        self.restart(needs)

    def configure(self, needs):
        newProject = False
        if not os.path.exists(os.path.join(self.module.env.local_conf_path)):
            newProject = True

        for need in needs:
            need.configure()
            need.copy_configuration()
            need.setup_needs()

        if newProject:
            raise Exception("""NOTICE: Default Configuration generated into {}.
            Review settings and configure any changes. Next run is live""".format(self.module.env.local_conf_path))

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
