from soppa.contrib import *

"""
Sentry is a Django-project using its own conventions including manage.py as sentry.

Assuming custom sentry.conf.py as project-specific ./conf.py
"""
from soppa.python import PythonDeploy

class Sentry(PythonDeploy):
    sentry_web='nginx'
    sentry_db='postgres'
    django_settings='conf'
    project='sentry'
    actions=['deploy',]
    required_settings=['sentry_servername']
    packages={
        'pip': ['sentry==6.4.4'],
    }
    needs=[
        'soppa.virtualenv',
        'soppa.redis',
        'soppa.factory',
        'soppa.pip',
        'soppa.operating',
        'soppa.template',
        'soppa.supervisor',
    ]

    def hook_start(self):
        if self.env.sentry_web=='nginx':
            self.add_need('soppa.nginx')

        if self.env.sentry_web=='apache':
            self.add_need('soppa.apache')

        if self.env.sentry_db=='mysql':
            self.add_need('soppa.mysql')

        if self.env.sentry_db=='postgres':
            self.add_need('soppa.postgres')

    def hook_pre_config(self):
        self.sudo('mkdir -p {www_root}htdocs')

        if self.env.sentry_web=='nginx':
            self.up('config/sentry_nginx.conf', '{nginx_dir}conf/sites-enabled/')

        if self.env.sentry_web=='apache':
            self.up('config/sentry_apache.conf', '{apache_dir}sites-enabled/')

        if self.has_need('supervisor'):
            self.up('config/sentry_supervisor.conf', '{supervisor_conf_dir}')


    def hook_pre(self):
        if unicode(self.env.get('dbengine')).find('mysql')!=-1:
            self.env.sentry_db = 'mysql'

        packages = []
        if self.env.sentry_db == 'postgres':
            packages.append('psycopg2==2.5.2')
        if self.env.sentry_db == 'mysql':
            packages.append('MySQL-python==1.2.5')
        self.pip.update_packages(packages=packages)

        self.factory.database(choice=self.env.sentry_db, action='setup')
        self.factory.webserver(choice=self.env.sentry_web, action='setup')

    def hook_post(self):
        self.up('config/conf.py', '{usedir}')

        self.factory.webserver(choice=self.env.sentry_web, action='restart')
        self.supervisor.restart()

sentry_task, sentry = register(Sentry)
