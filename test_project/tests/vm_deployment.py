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
    def xtest_mysql(self):
        state = dict(
            name='db',
            password=env.mysql_password,
            release_deploy_user='root',
            release_project='mysql',
        )
        r = Runner(state)
        r.setup(mysql(state))

    def xtest_django(self):
        state = dict(
            mysql_password=env.mysql_password,
            nginx_restart='always',
            release_project='helloworld',
            release_deploy_user='root',
        )
        r = Runner()
        r.setup(django(state))

    def test_graphite(self):
        # deployment configurations (override class defaults)
        config = dict(
            remote_user='root',
            release_deploy_user='root',
            release_project='graphite',
            release_host='graphite.dev',
        )
        # roles settings: config, hosts
        roles = dict(
            webservers=dict(
                config=dict(
                    http_port=80,
                    max_clients=200,
                    remote_user='root',),
                hosts=['web1','192.168.0.1']),
            atlanta=dict(
                hosts=['host1','host2']),
        )
        # host -specific settings
        hosts = dict(
            host1=dict(max_clients=199),
        ))
        # what to run in each host/role
        recipe = [
            dict(hosts='all', roles=['soppa.graphite']),
            dict(hosts='mongo_servers', roles=['soppa.mongod']
        ]
        Runner(config, hosts, roles, recipe).run()
        r = Runner()
        r.setup(graphite(config))

class SingleTestCase(BaseSuite):
    def xtest_grafana(self):
        state=dict(
            release_deploy_user='root',
            release_project='grafana',
            release_host='grafana.dev',
        )
        r = Runner()
        r.setup(grafana(state))

    def xtest_uwsgi(self):
        state=dict(
            release_project = 'uwsgitest',
            release_deploy_user='root',
        )
        r = Runner()
        r.setup(uwsgi(state))

class DeployTestCase(BaseSuite):
    def test_hello(self):
        self.assertEquals(1,1)

    def test_statsd(self):
        state=dict(
            release_project='statsd',)
        r = Runner()
        r.setup(statsd(state))

    def test_sentry(self):
        state=dict(
            release_project='sentry',
            servername='sentry.dev',
            postgres_name='sentry',
            postgres_user='sentry',
            postgres_password='sentry',)
        r = Runner()
        r.setup(sentry(state))

    def test_nginx(self):
        r = Runner()
        r.setup(nginx())

    def test_supervisor(self):
        r = Runner()
        r.setup(supervisor())

@task
def run_deployment_tests():
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream)
    alltests = unittest.TestSuite(
        map(unittest.makeSuite, [
            DjangoDeployTestCase,
            #DeployTestCase,
            #SingleTestCase,
    ]))
    result = runner.run(alltests)
    print 'Tests run ', result.testsRun
    pprint(result.errors)
    pprint(result.failures)
    stream.seek(0)
    print 'Test output\n', stream.read()

