import json, time, os, copy

from soppa.contrib import *
from soppa.alias import mlcd

env.runner_path = '{basepath}releases/runner.py'

cd = fabric_cd
sudo = fabric_sudo
run = fabric_run
put = fabric_put

class SilentEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError, e:
            return None

def to_json(data, cls=None):
    return json.dumps(data, encoding='utf-8', cls=cls, ensure_ascii=False, separators=(',',':'))

def run_cmd(cmd):#TODO:rename as remote_cmd
    from soppa.virtualenv import virtualenv
    from soppa.file import import_string
    sync_local_fabric_env()
    with virtualenv({}).activate() as a, cd(env.usedir) as b:
        if env.local_deployment:
            fn = import_string(cmd)
            fn()
        else:
            sudo(formatloc('python {runner_path} --cmd={cmd} --filename={sync_filename}'))
    # TODO: cleanup created sync.json that remains

def setup_runner(runner_path):
    from soppa.template import template
    tpl = template({})
    with mlcd('.'):
        tpl.up('runner.py', runner_path)
    sudo('chmod +x {0}'.format(runner_path))

def sync_local_fabric_env():
    """ Sync current fabric.env when running commands on a remote server
    - create dist/runner.py for executing remote commands
    """
    from soppa.template import template
    from soppa.file import file

    env.sync_filename = '/tmp/{0}_env.txt'.format(time.time())
    env_copy = copy.deepcopy(env)
    env_copy.use_ssh_config = False
    env_copy.host = False
    env_copy.host_string = False
    env_copy.local_deployment = True
    f = file({})
    tpl = template({})
    with f.tmpfile(to_json(env_copy, cls=SilentEncoder)) as f:
        tpl.up(f.name, env.sync_filename)

def use_fabric_env(path):
    path = path or env.sync_filename
    local_env = json.loads(open(path, 'r').read().strip() or '{}')
    env.update(**local_env)

def standalone_req():
    """ requires libraries to be in requirements.txt """
    from soppa.pip import install_package_global
    install_package_global('Fabric')
    install_package_global('Jinja2')

def run_cmd_alone(cmd):
    """ Run commands defined in local fabfile, on remote server, by copying fabfile and executing command there """
    put('fabfile.py', '/tmp/')

    standalone_req()

    with cd('/tmp'):
        run('python -c "from fabfile import *; execute({cmd});"'.format(cmd=cmd))
