import unittest, copy, os
from pprint import pprint
from StringIO import StringIO

from soppa.internal.ingredients import *
from soppa.internal.runner.default import *

env.password = ''
env.mysql_password = os.environ.get('MYSQL_PASS', '')

DEFAULT_HOSTS = ['box1']
DEFAULT_ROLES = dict(
all=dict(hosts=DEFAULT_HOSTS),
)

class BaseSuite(unittest.TestCase):
    pass

class DjangoDeployTestCase(BaseSuite):
    def test_mysql(self):
        config = dict(
            mysql_name='db',
            mysql_password=env.mysql_password,
            user='root',
            project='mysql',
        )
        roles = DEFAULT_ROLES
        recipe = [
            dict(roles='*', modules=['soppa.mysql']),
        ]
        Runner(config,{},roles,recipe).run()

    def test_django(self):
        config = dict(
            mysql_password=env.mysql_password,
            nginx_restart='always',
            project='helloworld',
            user='root',
        )
        roles = DEFAULT_ROLES
        recipe = [
            dict(roles='*', modules=['soppa.django']),
        ]
        Runner(config,{},roles,recipe).run()

    def test_graphite(self):
        config = dict(
            remote_user='root',
            user='root',
            project='graphite',
            host='graphite.dev',
        )
        # roles settings: config, hosts
        roles = dict(
            webservers=dict(
                config=dict(
                    http_port=80,
                    max_clients=200,
                    remote_user='root',),
                hosts=DEFAULT_HOSTS),
            dbservers=dict(
                hosts=DEFAULT_HOSTS),
        )
        # host -specific settings
        hosts = dict(
            host1=dict(max_clients=199),
        )
        # what to run in each host/role
        recipe = [
            dict(roles='*', modules=['soppa.graphite']),
            dict(roles='webservers', modules=['soppa.nginx']),]
        Runner(config, hosts, roles, recipe).run()

class SingleTestCase(BaseSuite):
    def test_grafana(self):
        config=dict(
            user='root',
            project='grafana',
            host='grafana.dev',
        )
        recipe = [dict(roles='*', modules=['soppa.grafana'])]
        Runner(config, {}, DEFAULT_ROLES, recipe).run()

    def test_uwsgi(self):
        config=dict(
            project = 'uwsgitest',
            user='root',
        )
        recipe = [dict(roles='*', modules=['soppa.uwsgi'])]
        Runner(config, {}, DEFAULT_ROLES, recipe).run()

class DeployTestCase(BaseSuite):
    def test_hello(self):
        self.assertEquals(1,1)

    def test_statsd(self):
        config = dict(
            project='statsd',
            user='root',
        )
        recipe = [dict(roles='*', modules=['soppa.statsd'])]
        Runner(config, {}, DEFAULT_ROLES, recipe).run()

    def test_sentry(self):
        config = dict(
            project='sentry',
            user='root',
            sentry_servername='sentry.dev',
            postgres_name='sentry',
            postgres_user='sentry',
            postgres_password='sentry',
        )
        recipe = [dict(roles='*', modules=['soppa.sentry'])]
        Runner(config, {}, DEFAULT_ROLES, recipe).run()

    def test_nginx(self):
        config = dict(
            user='root',
        )
        recipe = [dict(roles='*', modules=['soppa.nginx'])]
        Runner(config, {}, DEFAULT_ROLES, recipe).run()

    def test_supervisor(self):
        config = dict(
            user='root',
        )
        recipe = [dict(roles='*', modules=['soppa.supervisor'])]
        Runner(config, {}, DEFAULT_ROLES, recipe).run()

@task
def run_deployment_tests():
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream)
    alltests = unittest.TestSuite(
        map(unittest.makeSuite, [
            DjangoDeployTestCase,
            DeployTestCase,
            SingleTestCase,
    ]))
    result = runner.run(alltests)
    print 'Tests run ', result.testsRun
    pprint(result.errors)
    pprint(result.failures)
    stream.seek(0)
    print 'Test output\n', stream.read()

