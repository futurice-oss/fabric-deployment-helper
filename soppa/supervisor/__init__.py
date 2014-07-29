import os, time

from soppa.contrib import *
from soppa.deploy import DeployFrame

"""
Supervisor: http://supervisord.org/
"""

class Supervisor(DeployFrame):
    conf='/etc/supervisor/conf.d/'
    opt='-c "/etc/supervisord.conf"'
    user='{deploy_user}'

    version = 'supervisor==3.0'
    packages={'pip': [version]}
    needs=DeployFrame.needs+[
        'soppa.pip',
        'soppa.template',
        'soppa.virtualenv',
    ]

    def pre(self):
        self.pip.packages_as_local()
        self.pip.install_package_global(self.version)

        self.sudo('mkdir -p /etc/supervisor/conf.d/')
        self.sudo('mkdir -p /var/log/supervisor/')

        if self.operating.is_linux():
            self.up('init.d/supervisor', '/etc/init.d/')
            self.sudo('chmod +x /etc/init.d/supervisor')
            self.sudo('update-rc.d supervisor defaults')

    def hook_pre_config(self):
        self.up('supervisord.conf', '/etc/')
        
    @with_settings(warn_only=True)
    def startcmd(self):
        res = self.sudo("supervisorctl {opt} start all")
        if not res.succeeded or any(k in res for k in ['no such file', 'refused connection', 'SHUTDOWN_STATE']):
            if 'SHUTDOWN_STATE' in res:
                time.sleep(3)
            self.sudo("supervisord {opt}")

    @with_settings(warn_only=True)
    def stop(self):
        res = self.sudo("supervisorctl {opt} stop all")
        if not res.succeeded or any(k in res for k in ['SHUTDOWN_STATE']):
            time.sleep(3)
        self.sudo("supervisorctl {opt} shutdown")

    @with_settings(warn_only=True)
    def restart(self):
        self.hook_pre_config()#re-upload settings on restart
        self.stop()
        self.startcmd()

    @with_settings(warn_only=True)
    def soft_restart(self):
        # restart does not reload configurations?
        self.sudo("supervisorctl {opt} restart all")

    def check(self):
        result = self.sudo("supervisorctl {opt} status")


supervisor_task, supervisor = register(Supervisor)
