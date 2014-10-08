#encoding=utf8
import os, sys, time, copy, inspect, logging
from pprint import pprint as pp

from fabric.api import env, task, execute
from soppa.internal.tools import here, ObjectDict

class SoppaException(Exception):
    pass
env.abort_exception = SoppaException

# FABRIC
env.use_ssh_config = True
env.colorize_errors = True
env.user = 'root'# os.environ.get('USER', 'root')
# /FABRIC
env.CACHE = {}
env.ctx = {}
env.performed = {}

# Soppa
c = SOPPA_DEFAULTS = ObjectDict()
c.local_path = here(fn=inspect.getfile(sys._getframe(1)))

# ensure imports work the same for "fab task" and "python -m fabric task"
# by having the calling directory in sys.path
if c.local_path.rstrip('/') not in sys.path:
    sys.path.insert(0, c.local_path)

c.basedir = os.getcwd() + os.sep
c.soppadir = here()
c.config_dirs = ['config/',]
c.local_conf_path = 'config/'
c.abs_conf_path = os.path.join(c.local_path, c.local_conf_path)
c.installed_modules = [
'apache',
'apt',
'carbon',
'celery',
'collectd',
'contrib',
'django',
'dnsmasq',
'elasticsearch',
'file',
'firewall',
'git',
'grafana',
'graphite',
'internal',
'java',
'jinja',
'linux',
'mysql',
'nginx',
'nodejs',
'operating',
'package',
'pip',
'postgres',
'redis',
'remote',
'rsync',
'sentry',
'statsd',
'supervisor',
'template',
'uwsgi',
'vagrant',
'virtualenv',]

# order of package managers is execution order
c.packmans = [
    'soppa.internal.packagehandler.Apt',
    'soppa.internal.packagehandler.Pip',
    'soppa.internal.packagehandler.PipVenv',
]

DEFAULT_NS = ['config','soppa',]

