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

c.packmans = [
    'soppa.internal.packagehandler.Pip',
    'soppa.internal.packagehandler.PipVenv',
    'soppa.internal.packagehandler.Apt',]

DEFAULT_NS = ['config','soppa',]

