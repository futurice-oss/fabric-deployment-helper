from soppa.contrib import *

class Sentry(Soppa):
    """
    Sentry is a Django-project using its own conventions including manage.py as sentry.
    Assuming custom sentry.conf.py as project-specific ./conf.py
    """
    need_web = 'soppa.nginx'
    need_db = 'soppa.postgres'
    django_settings = 'conf'
    project = 'sentry'
    servername = 'sentry.dev'
    required_settings = [
            'sentry_servername',
            'need_web',
            'need_db']
    needs = ['soppa.virtualenv',
        'soppa.supervisor',
        'soppa.redis',
        'soppa.remote',

        'soppa.template',
        'soppa.pip',
        'soppa.apt',
    ]

    def setup(self):
        self.sudo('mkdir -p {www_root}htdocs')

        if self.has_need('nginx'):
            self.action('up', 'sentry_nginx.conf', '{nginx_conf_dir}', handler=['nginx.restart'])

        if self.has_need('apache'):
            self.action('up', 'sentry_apache.conf', '{apache_dir}sites-enabled/', handler=['apache.restart'])

        if self.has_need('supervisor'):
            self.action('up', 'sentry_supervisor.conf', '{supervisor_conf_dir}', handler=['supervisor.restart'])

        self.up('conf.py', '{path}')

