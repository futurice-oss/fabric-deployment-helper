import unittest, copy, os
from pprint import pprint
from StringIO import StringIO

from soppa.ingredients import *

env.password = ''
env.mysql_password = os.environ.get('MYSQL_PASS', '')

class BaseSuite(unittest.TestCase):
    pass

class DjangoDeployTestCase(BaseSuite):
    def test_mysql(self):
        ctx = dict(
            name='db',
            password='t44t',
        )
        s = mysql(ctx=ctx)
        s.setup()

    def test_django(self):
        env.ctx['mysql'] = {
            'password': env.mysql_password,
        }
        ctx = {
            'project':'helloworld',
        }
        state = dict(
                nginx=dict(restart='always'),
        )
        r = Runner(state)
        r.setup(django(ctx=ctx))

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
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream)
    alltests = unittest.TestSuite(
        tuple(unittest.makeSuite(case) for case in [
            DjangoDeployTestCase,
            DeployTestCase,
    ]))
    result = runner.run(alltests)
    print 'Tests run ', result.testsRun
    print 'Errors ', result.errors
    pprint(result.failures)
    stream.seek(0)
    print 'Test output\n', stream.read()

