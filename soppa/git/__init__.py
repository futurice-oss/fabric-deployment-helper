from soppa.contrib import *

class Git(Soppa):
    branch = 'master'
    dir = '{release.basepath}packages/'

    def fetch(self, repository, dest):
        with self.cd(dest):
            self.sudo('git pull {repository}'.format(repository=repository))

    def source(self):
        with tempfile.NamedTemporaryFile(delete=True, suffix='tar.gz') as f:
            release = f.name
            self.local('git archive --format=tar {branch} | gzip > {0}'.format(f.name))
            self.put(release, '{basepath}packages/')
            with self.cd('{basepath}'):
                self.run('tar zxf {package.dir}{release} -C {release_path}releases/{release}')

git_task, git = register(Git)
