import time

from soppa.contrib import *

class Supervisor(Soppa):
    """
    Supervisor: http://supervisord.org/
    """
    supervisor_conf_dir = '/etc/supervisor/conf.d/'
    supervisor_opt = '-c "/etc/supervisord.conf"'
    supervisor_user = '{root.user}'

    def setup(self):
        self.sudo('mkdir -p {supervisor_conf_dir}')
        self.sudo('mkdir -p /var/log/supervisor/')

        if self.operating.is_linux():
            self.up('init.d/supervisor', '/etc/init.d/')
            self.sudo('chmod +x /etc/init.d/supervisor')
            self.sudo('update-rc.d supervisor defaults')

        self.action('up', 'supervisord.conf', '/etc/', handler=['supervisor.restart'])
        
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
        self.stop()
        self.startcmd()

    @with_settings(warn_only=True)
    def soft_restart(self):
        # NOTE: supervisorctl restart does not reload configuration
        self.sudo("supervisorctl {supervisor_opt} restart all")

    def check(self):
        result = self.sudo("supervisorctl {supervisor_opt} status")

