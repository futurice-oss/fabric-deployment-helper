soppa
=====

Soppa - Sauce for Fabric.

Allows creating modules that do a single task for re-use.

QUICK START
===========

Either install as package, or `pip install -r requirements.txt` and done.
Run tests with `python setup.py test`.

Create tasks into a fabfile.py, eg (`fab graphite_deploy`; by default ~/.ssh/config in use):

Example: Install Graphite as defined in soppa.graphite:
```python
from soppa.ingredients import *
@task
def graphite_deploy():
    config = dict(
        project='graphite',
        deploy_user='root',
        host='graphite.dev',
    )
    roles = dict(all=dict(hosts=['vm']))
    recipe = [dict(roles='all', modules=['soppa.graphite'])]
    Runner(config,{},roles,recipe).run()
```
