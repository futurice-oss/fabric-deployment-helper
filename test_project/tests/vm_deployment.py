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
            password=env.mysql_password,
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
        env.project='statsd'
        r = Runner({})
        r.setup(statsd(ctx={}))

    def test_grafana(self):
        ctx = dict(
            project='grafana',
            soppa_is='download'
        )
        g = grafana(ctx=ctx)
        g.setup()

    def test_sentry(self):
        env.project = 'sentry'
        env.ctx = {
            'sentry': {
                'servername': 'sentry.dev',
            },
            'postgres': {
                'name': 'sentry',
                'user': 'sentry',
                'pass': 'sentry',
            }
        }
        r = Runner({})
        r.setup(sentry())

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
        map(unittest.makeSuite, [
            DjangoDeployTestCase,
            DeployTestCase,
    ]))
    result = runner.run(alltests)
    print 'Tests run ', result.testsRun
    print 'Errors ', result.errors
    pprint(result.failures)
    stream.seek(0)
    print 'Test output\n', stream.read()

