import os
from contextlib import contextmanager

from soppa.contrib import *

class Virtualenv(Soppa):
    """
    Setup for http://www.virtualenv.org/en/latest/
    """
    path='{www_root}{project}/venv/'
    is_active = True
    needs=[
        'soppa.pip',
    ]

    def setup(self):
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
