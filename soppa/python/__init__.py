from soppa.deploy import DeployFrame
from pprint import pprint as pp

class PythonDeploy(DeployFrame):
    tarball='/tmp/{release}.tar.gz'
    packages={}
    needs=DeployFrame.needs+[
        'soppa.virtualenv',
        'soppa.supervisor',
        'soppa.redis',
        'soppa.pip',
        'soppa.operating',
        'soppa.remote',
        ]

    def setup_needs(self):
        super(PythonDeploy, self).setup_needs()
        self.pip.update_packages()

    def pre(self):
        self.pip.setup()
        self.dirs()
        self.ownership()
        self.remote.setup_runner()

        self.usedir = self.fmt('{basepath}releases/{release}/')
        if not self.project:
            raise Exception("Define project")
        assert (self.release_time in self.usedir)

    def start(self):
        self.ask_sudo_password(capture=False)

    def configure(self):
        self.tar_from_git()
        self.upload_tar()
        self.pip.update_packages(packages=[])

    def post(self):
        self.ownership()
        self.symlink_release()

