import os
from contextlib import contextmanager

from soppa.contrib import *

class Virtualenv(Soppa):
    """
    Setup for http://www.virtualenv.org/en/latest/
    """
    path='{root.release.basepath}venv/'
    is_active = True
    needs=Soppa.needs+[
        'soppa.pip',
    ]

    def setup(self):
        if self.root.release.project is None:
            print "No project configured, skipping virtualenv setup"
            return
        with settings(warn_only=True):
            self.run('[ ! -d {path} ] && rm -rf {path} && '
                 'virtualenv'
                 ' --extra-search-dir={pip.packages_to}'
                 ' --prompt="({root.release.project})"'
                 ' {path}')

    def packages_path(self):
        with self.activate():
            rs = self.sudo("python -c 'from distutils.sysconfig import get_python_lib; print(get_python_lib())'")
            result = os.path.normpath(unicode(rs).strip()) + os.sep
        return result

    @contextmanager
    def activate(self):
        if not self.root.release.project:
            raise Exception('Project name not defined')
        if self.is_active:
            with self.prefix('source {path}bin/activate'):
                yield
        else:
            yield

virtualenv_task, virtualenv = register(Virtualenv)
