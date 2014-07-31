from soppa.contrib import *
from soppa.deploy import DeployFrame

class Nginx(DeployFrame):
    dir='/srv/nginx/'
    user=env.deploy_user
    group=env.deploy_group
    restart_command='/etc/init.d/nginx restart'
    start_command='/etc/init.d/nginx start'
    needs=[
        'soppa.operating',
        'soppa.template',
    ]

    def go(self):
        self.sudo('mkdir -p {nginx_dir}conf/sites-enabled/')
        
        if self.operating.is_linux():
            self.up('init.d/nginx', '/etc/init.d/')
            self.sudo('chmod 0755 /etc/init.d/nginx')
            self.sudo('chmod +x /etc/init.d/nginx')
            self.sudo('update-rc.d nginx defaults')
        if self.operating.is_osx():
            self.up('LaunchDaemons/nginx.plist', '/Library/LaunchDaemons/')
            self.sudo('chmod 0640 /Library/LaunchDaemons/nginx.plist')
            self.sudo('launchctl load /Library/LaunchDaemons/nginx.plist')
            
        if not self.exists('{nginx_dir}conf/mime.types'):
            self.sudo('cp {nginx_dir}conf/mime.types.default {nginx_dir}conf/mime.types')
        self.up('nginx.conf', '{nginx_dir}conf/')

        if not self.exists('{nginx_dir}sbin/nginx'):
            sctx = self.get_ctx()
            sctx['nginx_dir'] = self.dir.rstrip('/')
            self.up('nginx.bash', '/usr/src/')
            with self.cd('/usr/src/'):
                if self.operating.is_osx():
                    self.sudo('brew install pcre')
                self.sudo('bash nginx.bash')

    @with_settings(warn_only=True)
    def restart(self):
        if self.operating.is_linux():
            result = self.sudo(self.restart_command, pty=False)
            if result.failed:
                result = self.sudo(self.start_command, pty=False)
        if self.operating.is_osx():
            cmd = 'launchctl unload /Library/LaunchDaemons/nginx.plist '
            result = self.sudo(cmd)
            cmd = 'launchctl load /Library/LaunchDaemons/nginx.plist '
            result = self.sudo(cmd)

    @with_settings(warn_only=True)
    def stop(self):
        self.sudo('/etc/init.d/nginx stop')

nginx_task, nginx = register(Nginx)
