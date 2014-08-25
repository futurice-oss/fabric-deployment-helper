from soppa.contrib import *

class Git(Soppa):
    branch = 'master'

    def fetch(self, repository, dest):
        with self.cd(dest):
            self.sudo('git pull {repository}'.format(repository=repository))

    def source(self, branch=None):
        with tempfile.NamedTemporaryFile(delete=True, suffix='tar.gz') as f:
            self.local('git archive --format=tar {branch} | gzip > {filename}'.format(branch=branch or self.branch,
                filename=f.name))
            self.put(f.name, '{packages_path}')
            self.run('tar zxf {packages_path}{filename} -C {path}', filename=f.name)
