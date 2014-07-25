from soppa.contrib import *

"""
Sentry is a Django-project using its own conventions including manage.py as sentry.

Assuming custom sentry.conf.py as project-specific ./conf.py
"""
from soppa.python import PythonDeploy

class Sentry(PythonDeploy):
    web='nginx'
    db='postgres'
    django_settings='conf'
    project='sentry'
    actions=['deploy',]
    required_settings=['sentry_servername']
    packages={
        'pip': ['sentry==6.4.4'],
    }
    needs=PythonDeploy.needs+[
        'soppa.factory',
        'soppa.template',
    ]

    def hook_start(self):
        if self.web=='nginx':
            self.add_need('soppa.nginx')

        if self.web=='apache':
            self.add_need('soppa.apache')

        if self.db=='mysql':
            self.add_need('soppa.mysql')

        if self.db=='postgres':
            self.add_need('soppa.postgres')

    def hook_pre_config(self):
        self.sudo('mkdir -p {www_root}htdocs')

        if self.web=='nginx':
            self.up('sentry_nginx.conf', '{nginx_dir}conf/sites-enabled/')

        if self.web=='apache':
            self.up('sentry_apache.conf', '{apache_dir}sites-enabled/')

        if self.has_need('supervisor'):
            self.up('sentry_supervisor.conf', '{supervisor.conf}')


    def hook_pre(self):
        #if self.fmt('{django.dbengine}').find('mysql')!=-1:
        #    self.db = 'mysql'

        packages = []
        if self.db == 'postgres':
            packages.append('psycopg2==2.5.2')
        if self.db == 'mysql':
            packages.append('MySQL-python==1.2.5')
        self.pip.update_packages(packages=packages)

        self.factory.database(choice=self.db, action='setup')
        self.factory.webserver(choice=self.web, action='setup')

    def hook_post(self):
        self.up('conf.py', '{usedir}')

        self.factory.webserver(choice=self.web, action='restart')
        self.supervisor.restart()

sentry_task, sentry = register(Sentry)
