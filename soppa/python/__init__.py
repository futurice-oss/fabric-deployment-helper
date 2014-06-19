from soppa.deploy import DeployFrame

from soppa.remote import setup_runner

class PythonDeploy(DeployFrame):
    tarball='/tmp/{release}.tar.gz'
    packages={}
    needs=[
        'soppa.virtualenv',
        'soppa.supervisor',
        'soppa.redis',
        'soppa.pip',
        'soppa.operating',]

    def setup_needs(self):
        super(PythonDeploy, self).setup_needs()
        self.pip.update_packages()

    def pre(self):
        self.pip.setup()
        self.dirs()
        self.ownership()
        setup_runner(self.env.runner_path)

        self.env.usedir = '{basepath}releases/{release}/'
        if not self.env.project:
            raise Exception("Define project")
        assert (self.env.release_time in self.env.usedir)

    def start(self):
        self.ask_sudo_password(capture=False)

    def configure(self):
        self.tar_from_git()
        self.upload_tar()
        self.pip.update_packages(packages=[])

    def post(self):
        self.ownership()
        self.symlink_release()

