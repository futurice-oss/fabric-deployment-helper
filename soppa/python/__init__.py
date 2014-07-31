from soppa.deploy import DeployFrame
from pprint import pprint as pp

class PythonDeploy(DeployFrame):
    tarball='/tmp/{release}.tar.gz'
    needs=DeployFrame.needs+[
        'soppa.virtualenv',
        'soppa.supervisor',
        'soppa.redis',
        'soppa.pip',
        'soppa.remote',
        ]

    def pre(self):
        self.go()
        self.remote.setup_runner()

    def configure(self):
        self.tar_from_git()
        self.upload_tar()

    def post(self):
        self.ownership()
        self.symlink_release()

