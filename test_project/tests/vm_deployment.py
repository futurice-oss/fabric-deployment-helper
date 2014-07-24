import unittest, copy, os
from StringIO import StringIO

from soppa.ingredients import *

class BaseSuite(unittest.TestCase):
    pass

class DeployTestCase(BaseSuite):
    def test_hello(self):
        self.assertEquals(1,1)

    def test_statsd(self):
        ctx = dict(
            project='statsd',
        )
        g = statsd(ctx=ctx)
        g.setup()

    def test_grafana(self):
        ctx = dict(
            project='grafana',
            soppa_is='download'
        )
        g = grafana(ctx=ctx)
        g.setup()

    def test_sentry(self):
        env.sentry_servername = 'sentry.dev'
        #db = django().database_env('conf')
        env.ctx = {
            'sentry':
                {'project': 'sentry',
                'dbname': 'sentry',
                'dbuser': 'sentry',
                'dbpass': 'sentry',
                },
        }
        i = sentry({})
        i.setup()

    def test_graphite(self):
        env.project = 'graphite'
        ctx = {
            'project': 'graphite',
            'host': 'graphite.dev',
        }
        instance = graphite(ctx=ctx)
        instance.setup()

    def test_nginx(self):
        i = nginx()
        i.setup()

    def test_supervisor(self):
        i = supervisor()
        i.setup()

    def test_uwsgi(self):
        env.project = 'uwsgitest'
        i = uwsgi()
        i.setup()

@task
def run_deployment_tests():
    from pprint import pprint
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream)
    result = runner.run(unittest.makeSuite(DeployTestCase))
    print 'Tests run ', result.testsRun
    print 'Errors ', result.errors
    pprint(result.failures)
    stream.seek(0)
    print 'Test output\n', stream.read()

