#encoding=utf8
import os, sys, time, copy, inspect, logging
from pprint import pprint as pp

from fabric.api import env, task
from soppa.tools import here, ObjectDict

log = logging.getLogger('soppa')

# FABRIC
env.use_ssh_config = True
env.colorize_errors = True
env.user = 'root'# os.environ.get('USER', 'root')
# /FABRIC
env.CACHE = {}
env.ctx = {}

# Soppa
#c = SOPPA_DEFAULTS = ObjectDict()
c = env
c.local_project_root = here(fn=inspect.getfile(sys._getframe(1)))
c.basedir = os.getcwd() + os.sep
c.soppadir = here()

c.deploy_os = 'debian'
c.config_dirs = ['config/',]
c.local_conf_path = 'config/'

c.www_root = '/srv/www/'
c.basepath = '{www_root}{project}/'
c.project_root = '{basepath}/www/'

c.local_deployment = False
c.performed = {}
c.packmans = [
    'soppa.internal.packagehandler.Pip',
    'soppa.internal.packagehandler.PipVenv',
    'soppa.internal.packagehandler.Apt']

@task
def soppa_start():
    print "Soppa: Start"

@task
def soppa_end():
    print "Soppa: End"
    from soppa.contrib import dlog
    # TODO: save to a file on remote machine
    pp(dlog.data)

# insert 'always on' tasks
env.tasks.insert(0, 'soppa_start')
env.tasks.append('soppa_end')

