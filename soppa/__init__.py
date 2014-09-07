#encoding=utf8
import os, sys, time, copy, inspect, logging
from pprint import pprint as pp

from fabric.api import env, task, execute
from soppa.internal.tools import here, ObjectDict

# FABRIC
env.use_ssh_config = True
env.colorize_errors = True
env.user = 'root'# os.environ.get('USER', 'root')
# /FABRIC
env.CACHE = {}
env.ctx = {}
env.local_deployment = False
env.performed = {}

# Soppa
c = SOPPA_DEFAULTS = ObjectDict()
c.local_path = here(fn=inspect.getfile(sys._getframe(1)))
c.basedir = os.getcwd() + os.sep
c.soppadir = here()
c.config_dirs = ['config/',]
c.local_conf_path = 'config/'

c.packmans = [
    'soppa.internal.packagehandler.Pip',
    'soppa.internal.packagehandler.PipVenv',
    'soppa.internal.packagehandler.Apt',]

DEFAULT_NS = 'soppa'
