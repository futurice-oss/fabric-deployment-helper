from soppa.contrib import *
from soppa.alias import mlcd

from soppa.deploy import DeployFrame

class Uwsgi(DeployFrame):
    uwsgi_processes=2
    uwsgi_threads=2
    uwsgi_wsgi='{{project}}.wsgi:application'
    uwsgi_socket='127.0.0.1:5900'
    uwsgi_stats='127.0.0.1:9191'
    needs = [
        'soppa.virtualenv',
        'soppa.linux',
        'soppa.template',
        'soppa.pip',
    ]
    packages={
        'pip': ['uwsgi==2.0.4'],
    }

    def hook_pre(self):
        self.pip.update_packages()

    def hook_post(self):
        """ touch configs to reload, otherwise start uwsgi """
        self.up('config/uwsgi.ini', '{basepath}config/vassals/')
        self.sudo('chown -fR {deploy_user} {basepath}config/')
        if self.linux.running(r"ps auxww|grep uwsgi|grep [e]mperor"):
            with self.cd('{basepath}config/vassals/'):
                self.sudo("find . -maxdepth 1 -mindepth 1 -type f -exec touch {} \+")
        else:
            with self.virtualenv.activate() as a, self.cd(env.project_root) as b:
                self.sudo('uwsgi --emperor {basepath}config/vassals --uid {deploy_user} --gid {deploy_group} --daemonize {basepath}logs/{project}-emperor.log')

uwsgi_task, uwsgi = register(Uwsgi)
