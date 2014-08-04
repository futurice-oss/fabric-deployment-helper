from soppa.contrib import *

"""
Sentry is a Django-project using its own conventions including manage.py as sentry.

Assuming custom sentry.conf.py as project-specific ./conf.py
"""
from soppa.python import PythonDeploy

class Sentry(PythonDeploy):
    need_web='soppa.nginx'
    need_db='soppa.postgres'
    django_settings='conf'
    project='sentry'
    servername = 'sentry.dev'
    required_settings=[
            'sentry_servername',
            'need_web',
            'need_db']
    needs=PythonDeploy.needs+[
        'soppa.template',
    ]

    def go(self):
        self.sudo('mkdir -p {www_root}htdocs')

        if self.has_need('nginx'):
            self.nginx.up('sentry_nginx.conf', '{nginx_conf_dir}')

        if self.has_need('apache'):
            self.apache.up('sentry_apache.conf', '{apache_dir}sites-enabled/')

        if self.has_need('supervisor'):
            self.supervisor.up('sentry_supervisor.conf', '{supervisor_conf_dir}')

        self.up('conf.py', '{release_path}')

sentry_task, sentry = register(Sentry)
