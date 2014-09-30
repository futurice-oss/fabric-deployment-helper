from soppa.contrib import *

class Celery(Soppa):
    def setup(self):
        self.action('up', 'celery_supervisor.conf',
                '{supervisor_conf_dir}celery_supervisor_{project}.conf',
                handler=['supervisor.restart'],
                when=lambda x: x.soppa_proc_daemon=='supervisor',)
