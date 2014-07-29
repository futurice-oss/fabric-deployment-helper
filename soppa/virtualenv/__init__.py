import os

from soppa.contrib import *

from contextlib import contextmanager

"""
Setup for http://www.virtualenv.org/en/latest/
"""

class Virtualenv(Soppa):
    path='{www_root}{project}/venv/'
    version='virtualenv==1.11.4'
    is_active = True
    packages={
        'pip': 'config/requirements.txt',
    }
    needs=[
        'soppa.pip',
    ]

    def setup(self):
        self.pip.packages_as_local(packages=[self.version])
        self.pip.install_package_global(self.version)

        with settings(warn_only=True):
            self.run('[ ! -d {path} ] && rm -rf {path} && '
                 'virtualenv'
                 ' --extra-search-dir={pip.packages_to}'
                 ' --prompt="({project})"'
                 ' {path}'.format(**self.get_ctx()))

    def packages_path(self):
        with self.activate():
            result = os.path.normpath(self.sudo("python -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())'").strip()) + os.sep
        return result

    @contextmanager
    def activate(self):
        if self.is_active:
            with self.prefix('source {path}bin/activate'):
                yield
        else:
            yield

virtualenv_task, virtualenv = register(Virtualenv)
