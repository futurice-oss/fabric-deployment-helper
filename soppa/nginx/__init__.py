import copy

from soppa.contrib import *
from soppa.alias import mlcd
from soppa.deploy import DeployFrame

class Nginx(DeployFrame):
    nginx_dir='/srv/nginx/'
    nginx_user=env.deploy_user
    nginx_group=env.deploy_group
    nginx_restart_command='/etc/init.d/nginx restart'
    nginx_start_command='/etc/init.d/nginx start'
    needs=[
        'soppa.operating',
        'soppa.template',
    ]

    def pre(self):
        if not self.exists('{nginx_dir}sbin/nginx'):
            sctx = self.get_ctx()
            sctx['nginx_dir'] = self.env.nginx_dir.rstrip('/')
            self.up('config/nginx.bash', '/usr/src/')
            with self.cd('/usr/src/'):
                if self.operating.is_osx():
                    self.sudo('brew install pcre')
                self.sudo('bash nginx.bash')

    def hook_pre_config(self):
        self.sudo('mkdir -p {nginx_dir}conf/sites-enabled/')
        
        if self.operating.is_linux():
            self.up('config/init.d/nginx', '/etc/init.d/')
            self.sudo('chmod 0755 /etc/init.d/nginx')
            self.sudo('chmod +x /etc/init.d/nginx')
            self.sudo('update-rc.d nginx defaults')
        if self.operating.is_osx():
            self.up('config/LaunchDaemons/nginx.plist', '/Library/LaunchDaemons/')
            self.sudo('chmod 0640 /Library/LaunchDaemons/nginx.plist')
            self.sudo('launchctl load /Library/LaunchDaemons/nginx.plist')
            
        self.up('config/nginx.conf', '{nginx_dir}conf/')

    @with_settings(warn_only=True)
    def restart(self):
        if self.operating.is_linux():
            result = self.sudo(self.env.nginx_restart_command, pty=False)
            if result.failed:
                result = self.sudo(self.env.nginx_start_command, pty=False)
        if self.operating.is_osx():
            cmd = 'launchctl unload /Library/LaunchDaemons/nginx.plist '
            result = self.sudo(cmd)
            cmd = 'launchctl load /Library/LaunchDaemons/nginx.plist '
            result = self.sudo(cmd)

    @with_settings(warn_only=True)
    def stop(self):
        self.sudo('/etc/init.d/nginx stop')

nginx_task, nginx = register(Nginx)
