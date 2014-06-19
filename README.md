soppa
=====

Soppa - Sauce for Fabric.


Either install as package, or 'pip install -r requirements.txt' and done.
Run tests with 'python setup.py test'.

Create tasks into a fabfile.py, eg (fab -H target graphite_deploy; by default ~/.ssh/config in use):

from soppa.ingredients import *
@task
def graphite_deploy():
    # Install Graphite as defined in soppa/graphite
    ctx = {
        'project': 'graphite',
        'graphite_servername': 'graphite.dev',
    }
    i = graphite(ctx=ctx)
    i.setup()

HOW DOES IT WORK?
=================

1. Deployables extend Soppa
 - .get_ctx() combines global and local context to be able to deploy multiple things at once.
 - Fabric functionality is tied to class methods (sudo -> self.sudo), to run in correct context
 - .setup() is the single entrypoint to get the deployable up/updated.
 - Dependencies in needs=[] (other deployables) and packages={} (apt-get, pip, ...)

2. Configuration templates in config/ directory of deployables
 - overrides placed into a local config/ directory

3. Context can be global or instance specific
 - Global: env.ctx= {'sentry': {'project': 'myproject'},
            {'postgres': {'user': 'bob'}}}
 - Instance: sentry(dict(project='myproject'))

4. Can deploy locally on OSX by calling aslocal()
 - sudo, run will map to local

