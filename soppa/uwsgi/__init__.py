from soppa.contrib import *

from soppa.deploy import DeployFrame

class Uwsgi(DeployFrame):
    processes=2
    threads=2
    wsgi='{project}.wsgi:application'
    socket='127.0.0.1:5900'
    stats='127.0.0.1:9191'
    needs = DeployFrame.needs+[
        'soppa.virtualenv',
        'soppa.linux',
        'soppa.template',
        'soppa.pip',
    ]

    def go(self):
        """ touch configs to reload, otherwise start uwsgi """
        self.sudo('mkdir -p {basepath}config/vassals')
        self.up('uwsgi.ini', '{basepath}config/vassals/')
        self.sudo('chown -fR {deploy_user} {basepath}config/')

    def restart(self):
        if self.linux.running(r"ps auxww|grep uwsgi|grep [e]mperor"):
            self.cmd_restart()
        else:
            self.cmd_start()

    def cmd_restart(self):
        with self.cd('{basepath}config/vassals/'):
            self.sudo("find . -maxdepth 1 -mindepth 1 -type f -exec touch {} \+")

    def cmd_start(self):
        with self.virtualenv.activate():
            self.sudo('uwsgi --emperor {basepath}config/vassals --uid {deploy_user} --gid {deploy_group} --daemonize {basepath}logs/{project}-emperor.log')

uwsgi_task, uwsgi = register(Uwsgi)
