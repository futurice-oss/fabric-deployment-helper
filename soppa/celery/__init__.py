from soppa.contrib import *

class Celery(Soppa):
    needs=[
        'soppa.template',
        'soppa.supervisor',
    ]

    def go(self):
        self.up('celery_supervisor.conf',
                '{supervisor.conf_dir}celery_supervisor_{project}.conf')

celery_task, celery = register(Celery)
