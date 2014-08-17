import time

from soppa.contrib import *


class Supervisor(Soppa):
    """
    Supervisor: http://supervisord.org/
    """
    conf_dir='/etc/supervisor/conf.d/'
    opt='-c "/etc/supervisord.conf"'
    user='{root.deploy_user}'

    needs=[
        'soppa.file',
        'soppa.operating',
        'soppa.pip',
        'soppa.template',
        'soppa.virtualenv',
    ]

    def go(self):
        self.sudo('mkdir -p {supervisor_conf_dir}')
        self.sudo('mkdir -p /var/log/supervisor/')

        if self.operating.is_linux():
            self.up('init.d/supervisor', '/etc/init.d/')
            self.sudo('chmod +x /etc/init.d/supervisor')
            self.sudo('update-rc.d supervisor defaults')

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
        self.stop()
        self.startcmd()

    @with_settings(warn_only=True)
    def soft_restart(self):
        # NOTE: supervisorctl restart does not reload configuration
        self.sudo("supervisorctl {opt} restart all")

    def check(self):
        result = self.sudo("supervisorctl {opt} status")


supervisor_task, supervisor = register(Supervisor)
