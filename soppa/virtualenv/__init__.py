import os
from contextlib import contextmanager

from soppa.contrib import *

class Virtualenv(Soppa):
    """
    Setup for http://www.virtualenv.org/en/latest/
    """
    virtualenv_path = '{root.basepath}venv/'
    virtualenv_active = True
    needs = Soppa.needs+[
        'soppa.pip',
    ]

    def setup(self):
        if self.root.project is None:
            print "No project configured, skipping virtualenv setup"
            return
        if not self.exists(self.virtualenv_path):
            self.run('virtualenv'
                 ' --extra-search-dir={pip.packages_to}'
                 ' --prompt="({root.project})"'
                 ' {virtualenv_path}')

    def packages_path(self):
        with self.activate():
            rs = self.sudo("python -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())'")
            result = os.path.normpath(unicode(rs).strip()) + os.sep
        return result

    @contextmanager
    def activate(self):
        if not self.root.project:
            raise Exception('Project name not defined')
        if self.virtualenv_active:
            with self.prefix('source {virtualenv_path}bin/activate'):
                yield
        else:
            yield

virtualenv_task, virtualenv = register(Virtualenv)
