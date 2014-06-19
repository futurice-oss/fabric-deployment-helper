import os

from soppa.contrib import *

from contextlib import contextmanager

"""
Setup for http://www.virtualenv.org/en/latest/
"""

class Virtualenv(Soppa):
    virtualenv_dir='{www_root}{project}/venv/'
    virtualenv_version='1.11.4'
    is_active = True
    packages={
        'pip': 'config/requirements.txt',
    }
    needs=[
        'soppa.pip',
    ]

    def setup(self):
        self.pip.install_package_global('virtualenv=={virtualenv_version}'.format(**self.get_ctx()))

        with settings(warn_only=True):
            self.run('[ ! -d {virtualenv_dir} ] && rm -rf {virtualenv_dir} && '
                 'virtualenv'
                 ' --extra-search-dir={pip_python_packages_dir}'
                 ' --prompt="({project})"'
                 ' {virtualenv_dir}'.format(**self.get_ctx()))

    def packages_path(self):
        with self.activate():
            result = os.path.normpath(self.sudo("python -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())'").strip()) + os.sep
        return result

    @contextmanager
    def activate(self):
        if self.is_active:
            with self.prefix('source {0}bin/activate'.format(self.env.virtualenv_dir)):
                yield
        else:
            yield

virtualenv_task, virtualenv = register(Virtualenv)
