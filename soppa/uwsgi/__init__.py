from soppa.contrib import *

class Uwsgi(Soppa):
    processes=2
    threads=2
    wsgi='{project}.wsgi:application'
    socket='127.0.0.1:5900'
    stats='127.0.0.1:9191'
    needs = [
        'soppa.file',
        'soppa.operating',
        'soppa.virtualenv',
        'soppa.linux',
        'soppa.template',
        'soppa.pip',
    ]
    need_release = {
        'project': 'uwsgi',
    }
    conf_dir = '{release.basepath}config/vassals/'

    def go(self):
        """ touch configs to reload, otherwise start uwsgi """
        self.sudo('mkdir -p {release.basepath}config/vassals/')
        self.up('uwsgi.ini', '{release.basepath}config/vassals/')
        self.sudo('chown -fR {deploy_user} {release.basepath}config/')

    def restart(self):
        if self.linux.running(r"ps auxww|grep uwsgi|grep [e]mperor"):
            self.cmd_restart()
        else:
            self.cmd_start()

    def cmd_restart(self):
        with self.cd('{release.basepath}config/vassals/'):
            self.sudo("find . -maxdepth 1 -mindepth 1 -type f -exec touch {} \+")

    def cmd_start(self):
        with self.virtualenv.activate():
            self.sudo('uwsgi --emperor {release.basepath}config/vassals --uid {release.deploy_user} --gid {release.deploy_group} --daemonize {release.basepath}logs/{release.project}-emperor.log')

uwsgi_task, uwsgi = register(Uwsgi)
