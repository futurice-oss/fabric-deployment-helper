import os
from contextlib import contextmanager

from soppa.contrib import *

class Virtualenv(Soppa):
    """
    Setup for http://www.virtualenv.org/en/latest/
    """
    virtualenv_path = '{root.basepath}venv/'
    virtualenv_default_package = 'virtualenv==1.11.4'

    def setup(self):
        self.pip.setup()
        if not self.exists(self.virtualenv_path):
            self.sudo('virtualenv'
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
        with self.prefix('source {virtualenv_path}bin/activate'):
            yield
