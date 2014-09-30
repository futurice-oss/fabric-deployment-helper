from soppa.contrib import *
import tempfile

class Git(Soppa):
    branch = 'master'

    def setup(self):
        self.sudo('mkdir -p {packages_path}')

    def fetch(self, repository, dest):
        with self.cd(dest):
            self.sudo('git pull {repository}'.format(repository=repository))

    def source(self, to, branch=None):
        with tempfile.NamedTemporaryFile(delete=True, suffix='tar.gz') as f:
            self.local('git archive --format=tar {branch} | gzip > {filename}'\
                    .format(branch=branch or self.branch, filename=f.name))
            remote_name = self.put(f.name, '{packages_path}')
            self.sudo('tar zxf {filename} -C {to}', filename=remote_name[0], to=to)
