#encoding=utf8
import os, sys, time, copy, inspect, logging
from pprint import pprint as pp

from fabric.api import env, task
from soppa.tools import here

log = logging.getLogger('soppa')

# GLOBALS
env.ctx = {}
env.local_project_root = here(fn=inspect.getfile(sys._getframe(1)))
env.basedir = os.getcwd() + os.sep
env.soppadir = here()

env.DEBUG = False
env.TESTING = False
env.colorize_errors = True
env.deploy_os = 'debian'
env.deploy_user = 'www-data'
env.deploy_group = 'www-data'
env.deploy_tarball='/tmp/{release}.tar.gz'
env.user = os.environ.get('USER', None)
env.owner = 'www-data'
env.config_dirs = ['config/',]
env.local_conf_path = 'config/'

env.soppa_is = 'git'

env.release_time = time.strftime('%Y%m%d%H%M%S')
env.pkg = '/tmp/{release}.tar.gz'
env.release = '{release_time}'
env.release_symlink_path = 'releases/{release}'

env.project = None # set in fabfile *only*
env.www_root = '/srv/www/'
env.basepath = '{www_root}{project}/'
env.project_root = '{www_root}{project}/www/'
env.usedir = '{project_root}'

env.branch = 'master'

env.use_ssh_config = True

env.local_deployment = False
env.performed = {}

@task
def soppa_start():
    print "Soppa: Start"

@task
def soppa_end():
    print "Soppa: End"
    if env.possible_bugged_strings:
        print "Possible badly interpreted strings:"
        pp(env.possible_bugged_strings)

    if env.ctx_failure:
        print "Possible context bugs:"
        pp(env.ctx_failure)

# insert 'always on' tasks
env.tasks.insert(0, 'soppa_start')
env.tasks.append('soppa_end')

