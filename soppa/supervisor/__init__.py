import os, time

from soppa.contrib import *
from soppa.deploy import DeployFrame

"""
Supervisor: http://supervisord.org/
"""

class Supervisor(DeployFrame):
    supervisor_conf_dir='/etc/supervisor/conf.d/'
    supervisor_opt='-c "/etc/supervisord.conf"'
    supervisor_user='{deploy_user}'
    packages={'pip': ['supervisor==3.0']}
    needs=[
        'soppa.pip',
        'soppa.operating',
        'soppa.template',
        'soppa.virtualenv',
    ]

    def pre(self):
        self.pip.sync_packages()
        self.pip.install_package_global('supervisor')

        self.sudo('mkdir -p /etc/supervisor/conf.d/')
        self.sudo('mkdir -p /var/log/supervisor/')

        if self.operating.is_linux():
            self.up('config/init.d/supervisor', '/etc/init.d/')
            self.sudo('chmod +x /etc/init.d/supervisor')
            self.sudo('update-rc.d supervisor defaults')

    def hook_pre_config(self):
        sctx = self.get_ctx()
        self.up('config/supervisord.conf', '/etc/')

    def hook_post(self):
        self.restart()
        
    @with_settings(warn_only=True)
    def startcmd(self):
        res = self.sudo("supervisorctl {supervisor_opt} start all")
        if not res.succeeded or any(k in res for k in ['no such file', 'refused connection', 'SHUTDOWN_STATE']):
            if 'SHUTDOWN_STATE' in res:
                time.sleep(3)
            self.sudo("supervisord {supervisor_opt}")

    @with_settings(warn_only=True)
    def stop(self):
        res = self.sudo("supervisorctl {supervisor_opt} stop all")
        if not res.succeeded or any(k in res for k in ['SHUTDOWN_STATE']):
            time.sleep(3)
        self.sudo("supervisorctl {supervisor_opt} shutdown")

    @with_settings(warn_only=True)
    def restart(self):
        self.hook_pre_config()#re-upload setings on restart
        self.stop()
        self.startcmd()

    @with_settings(warn_only=True)
    def soft_restart(self):
        # restart does not reload configurations?
        self.sudo("supervisorctl {supervisor_opt} restart all")

    def check(self):
        result = self.sudo("supervisorctl {supervisor_opt} status")


supervisor_task, supervisor = register(Supervisor)
