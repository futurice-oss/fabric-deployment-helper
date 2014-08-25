from soppa.contrib import *

class Celery(Soppa):
    needs=[
        'soppa.template',
        'soppa.supervisor',
    ]

    def setup(self):
        self.action('up', 'celery_supervisor.conf',
                '{supervisor.conf_dir}celery_supervisor_{project}.conf',
                handler=['supervisor.restart'])
