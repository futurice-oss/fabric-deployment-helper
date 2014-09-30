from soppa.contrib import *

class Sentry(Soppa):
    """
    Sentry is a Django-project using its own conventions including manage.py as sentry.
    Assuming custom sentry.conf.py as project-specific ./conf.py
    """
    django_settings = 'conf'
    project = 'sentry'
    servername = 'sentry.dev'
    path = '{basepath}'

    def setup(self):
        self.virtualenv.setup()
        self.postgres.setup()

        self.sudo('mkdir -p {www_root}htdocs')
        self.up('conf.py', '{path}')

        self.action('up', 'sentry_nginx.conf', '{nginx_conf_dir}',
                handler=['nginx.restart'],
                when=lambda x: x.soppa_web_server=='nginx')

        self.action('up', 'sentry_apache.conf', '{apache_dir}sites-enabled/',
                handler=['apache.restart'],
                when=lambda x: x.soppa_web_server=='apache')

        self.action('up', 'sentry_supervisor.conf', '{supervisor_conf_dir}',
                handler=['supervisor.restart'],
                when=lambda x: x.soppa_proc_daemon=='supervisor')

