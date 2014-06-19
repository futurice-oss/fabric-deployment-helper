from soppa.ingredients import *

@task
def graphite_deploy():
    ctx = {
        'project': 'graphite',
        'graphite_servername': 'graphite.dev',
    }
    i = graphite(ctx=ctx)
    i.setup()
