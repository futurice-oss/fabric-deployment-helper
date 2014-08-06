import unittest, copy, os
from pprint import pprint
from StringIO import StringIO

from soppa.internal.ingredients import *
from soppa.internal.runner.default import *

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
        state = {}
        r = Runner(state)
        r.setup(mysql(ctx=ctx))

    def test_django(self):
        env.ctx['mysql'] = {
            'password': env.mysql_password,
        }
        env.project = 'helloworld'
        ctx = {}
        state = dict(
            nginx=dict(restart='always'),
        )
        r = Runner(state)
        r.setup(django(ctx=ctx))

    def test_graphite(self):
        env.project = 'graphite'
        ctx = {
            'host': 'graphite.dev',
        }
        r = Runner()
        r.setup(graphite(ctx=ctx))

class SingleTestCase(BaseSuite):
    def test_grafana(self):
        state=dict(
            release_deploy_user='root',
            release_project='grafana',
            release_host='grafana.dev',
        )
        r = Runner()
        g = grafana(state)
        r.setup(g)

class DeployTestCase(BaseSuite):
    def test_hello(self):
        self.assertEquals(1,1)

    def test_statsd(self):
        env.project='statsd'
        r = Runner()
        r.setup(statsd())

    def test_sentry(self):
        env.project = 'sentry'
        env.ctx = {
            'sentry': {
                'servername': 'sentry.dev',
            },
            'postgres': {
                'name': 'sentry',
                'user': 'sentry',
                'password': 'sentry',
            }
        }
        r = Runner()
        r.setup(sentry())

    def test_nginx(self):
        r = Runner()
        r.setup(nginx())

    def test_supervisor(self):
        r = Runner()
        r.setup(supervisor())

    def test_uwsgi(self):
        env.project = 'uwsgitest'
        r = Runner()
        r.setup(uwsgi())

@task
def run_deployment_tests():
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream)
    alltests = unittest.TestSuite(
        map(unittest.makeSuite, [
            #DjangoDeployTestCase,
            #DeployTestCase,
            SingleTestCase,
    ]))
    result = runner.run(alltests)
    print 'Tests run ', result.testsRun
    pprint(result.errors)
    pprint(result.failures)
    stream.seek(0)
    print 'Test output\n', stream.read()

