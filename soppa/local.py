import os

from fabric.api import env, task

@task
def aslocal(prompt=True):
    env.local_deployment = True
    # reset any remote settings
    env.host = 'localhost'
    env.host_string = None
    env.hosts = []

    from soppa.operating import operating
    operating = operating(env)
    if operating.is_a('darwin'):
        osx()

    if prompt:
        from soppa.deploy import DeployFrame
        dep = DeployFrame()
        dep.ask_sudo_password()

@task
def osx():
    # NOTE: needs to be called before instantiation of recipes
    # OSX
    env.use_sudo = True
    env.user = os.environ['USER']
    env.owner = env.user
    env.deploy_user = env.owner
    env.deploy_group = 'wheel'
    env.local_deployment = True

    env.ctx.setdefault('nginx', {})
    env.ctx['nginx']['user'] ='nobody'
    env.ctx['nginx']['group'] = env.deploy_group
    env.ctx.setdefault('supervisor', {})
    env.ctx['supervisor']['user'] = 'nobody'

    env.shell = "/bin/bash -c" # default: -l -c
    # MySQL-python will fail due unknown compiler flags in OSX Mavericks
    os.environ['CFLAGS'] = '-Qunused-arguments'
    os.environ['CPPFLAGS'] = '-Qunused-arguments'
    # to run Django commands from fabfile need settings configured
    os.environ['DJANGO_SETTINGS_MODULE'] = getattr(env, 'django_settings', 'settings')
