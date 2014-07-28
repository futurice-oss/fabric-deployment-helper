from soppa.contrib import *

"""
Setup for https://pypi.python.org/pypi/nodeenv
- requires nodeenv to be in requirements.txt
"""

class NodeJS(Soppa):
    version='0.10.29'
    binary_dir='{basepath}venv/bin/'
    pkg={
        'pip': 'config/requirements.txt'
    }
    needs=[
        'soppa.pip',
        'soppa.virtualenv',
    ]
    symlink_npm = ['lessc',]

    def setup(self):
        with self.virtualenv.activate():
            self.pip.install_package_global('nodeenv')

            with self.cd('{basepath}'):
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
        with self.cd('{basepath}'):
            for symlinked_binary in self.symlink_npm:
                self.sudo(self.fmt('ln -sf $(pwd)/node_modules/.bin/{symlinked_binary} {nodejs_binary_dir}', symlinked_binary=symlinked_binary))

nodejs_task, nodejs = register(NodeJS)
