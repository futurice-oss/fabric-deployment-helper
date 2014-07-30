from soppa.contrib import *

class NodeJS(Soppa):
    """
    Setup for https://pypi.python.org/pypi/nodeenv
    """
    version='0.10.29'
    binary_dir='{basepath}venv/bin/'
    needs=[
        'soppa.pip',
        'soppa.virtualenv',
    ]
    symlink_npm = ['lessc',]

    def setup(self):
        with self.virtualenv.activate(), self.cd('{basepath}'):
            self.sudo('[ -f "{nodejs_binary_dir}node" ] || nodeenv -p --node={nodejs_version}')

        with self.virtualenv.activate():
            with settings(warn_only=True):
                with self.cd('{usedir}'):
                    self.sudo('cp {usedir}package.json {basepath}')
                    self.sudo('ln -sf {basepath}node_modules .')
            with settings(warn_only=True):
                with self.cd('{basepath}'):
                    self.sudo('npm install')
                
        self.symlink_node_binaries()

    def symlink_node_binaries(self):
        """ NPM package.json installations are not symlinked to project by default """
        with self.cd('{basepath}'):
            for symlinked_binary in self.symlink_npm:
                self.sudo(self.fmt('ln -sf $(pwd)/node_modules/.bin/{symlinked_binary} {nodejs_binary_dir}', symlinked_binary=symlinked_binary))

nodejs_task, nodejs = register(NodeJS)
