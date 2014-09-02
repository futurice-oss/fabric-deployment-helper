from contextlib import contextmanager
import os, inspect, sys

from fabric.api import env
from soppa import here

@contextmanager
def mlcd(path):
    """ Move to a local directory """
    calling_file = inspect.getfile(sys._getframe(2))
    d = here(path, fn=calling_file)
    try:
        yield os.chdir(d)
    finally:
        os.chdir(env.basedir)

