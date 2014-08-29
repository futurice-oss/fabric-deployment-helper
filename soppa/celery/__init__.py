from soppa.contrib import *

class Celery(Soppa):
    def setup(self):
        pass

    def configure_supervisor(self):
        self.action('up', 'celery_supervisor.conf',
                '{supervisor.conf_dir}celery_supervisor_{project}.conf',
                handler=['supervisor.restart'])
