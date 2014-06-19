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

