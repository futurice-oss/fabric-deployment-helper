from soppa.contrib import *

class Uwsgi(Soppa):
    """
    UWSGI is installed into a virtual environment, with configs going under parent, when isntalled as a need.
    """
    processes = 2
    threads = 2
    wsgi = '{root.project}.wsgi:application'
    socket = '127.0.0.1:5900'
    stats = '127.0.0.1:9191'
    needs = Soppa.needs+[
        'soppa.file',
        'soppa.operating',
        'soppa.virtualenv',
        'soppa.linux',
        'soppa.template',
        'soppa.pip',
        'soppa.apt',
    ]
    project = 'uwsgi'
    conf_dir = '{root.basepath}config/'

    def setup(self):
        self.sudo('mkdir -p {conf_dir}vassals/')
        self.sudo('chown -fR {root.deploy_user} {root.basepath}config/')
        self.action('up', 'uwsgi.ini', '{conf_dir}vassals/', handler=['uwsgi.restart'])

    def restart(self):
        if self.linux.running(r"ps auxww|grep uwsgi|grep [e]mperor"):
            self.cmd_restart()
        else:
            self.cmd_start()

    def cmd_restart(self):
        with self.cd('{conf_dir}vassals/'):
            self.sudo("find . -maxdepth 1 -mindepth 1 -type f -exec touch {} \+")

    def cmd_start(self):
        with self.virtualenv.activate():
            self.sudo('uwsgi --emperor {conf_dir}vassals --uid {root.deploy_user} --gid {root.deploy_group} --daemonize {root.basepath}logs/{root.project}-emperor.log')

uwsgi_task, uwsgi = register(Uwsgi)
