#encoding=utf8
import os, sys, time, copy, inspect, logging
from pprint import pprint as pp

from fabric.api import env, task

log = logging.getLogger('soppa')

def here(path=None, fn=None, instance=None):
    """ Evaluate path relative to where function was called
    fn = provide scope ('source')
    """
    if instance:
        calling_file = inspect.getfile(instance.__class__)
    elif fn:
        calling_file = fn
    else:
        calling_file = inspect.getfile(sys._getframe(1)) # relative or absolute return value
    calling_file = os.path.abspath(calling_file)
    subfolder = path.lstrip('/') if path else ''
    return os.path.join(os.path.dirname(calling_file), subfolder)

env.ctx = {}
env.local_project_root = here(fn=inspect.getfile(sys._getframe(1)))
env.basedir = os.getcwd() + os.sep

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

env.soppa_is = 'git'

env.release_time = time.strftime('%Y%m%d%H%M%S')
env.pkg = '/tmp/{release}.tar.gz'
env.release = '{release_time}'
env.release_symlink_path = 'releases/{release}'

env.dbpass = None
env.dbuser = None

env.project = None# set in fabfile *only*
env.www_root = '/srv/www/'
env.basepath = '{www_root}{project}/'
env.project_root = '{www_root}{project}/www/'
env.usedir = '{project_root}'

env.branch = 'master'

env.use_ssh_config = True

env.local_deployment = False

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

