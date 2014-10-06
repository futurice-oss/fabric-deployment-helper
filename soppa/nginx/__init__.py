from soppa.contrib import *

class Nginx(Soppa):
    path = '/srv/nginx/'
    user = 'www-data'
    group = 'www-data'
    restart_command = '/etc/init.d/nginx restart'
    start_command = '/etc/init.d/nginx start'
    conf_dir = '{path}conf/sites-enabled/'

    def setup(self):
        self.sudo('mkdir -p {nginx_conf_dir}')
        
        if self.operating.is_linux():
            self.up('init.d/nginx', '/etc/init.d/')
            self.sudo('chmod 0755 /etc/init.d/nginx')
            self.sudo('chmod +x /etc/init.d/nginx')
            self.sudo('update-rc.d nginx defaults')
        if self.operating.is_osx():
            self.up('LaunchDaemons/nginx.plist', '/Library/LaunchDaemons/')
            self.sudo('chmod 0640 /Library/LaunchDaemons/nginx.plist')
            self.sudo('launchctl load /Library/LaunchDaemons/nginx.plist')

        if not self.exists('{path}sbin/nginx'):
            if not self.exists('{path}sbin/nginx/nginx.bash'):
                self.up('nginx.bash', '/usr/src/', ctx=dict(nginx_path=self.path.rstrip('/')))
            if self.operating.is_osx():
                self.run('brew install pcre', use_sudo=False)
            with self.cd('/usr/src/'):
                self.sudo('bash nginx.bash')
            
        if not self.exists('{path}conf/mime.types'):
            self.sudo('cp {path}conf/mime.types.default {path}conf/mime.types')

        self.action('up', 'nginx.conf', '{path}conf/', handler=['nginx.restart'])

    @with_settings(warn_only=True)
    def restart(self):
        if self.operating.is_linux():
            result = self.sudo(self.nginx_restart_command, pty=False)
            if result.failed:
                result = self.sudo(self.nginx_start_command, pty=False)
        if self.operating.is_osx():
            cmd = 'launchctl unload /Library/LaunchDaemons/nginx.plist '
            result = self.sudo(cmd)
            cmd = 'launchctl load /Library/LaunchDaemons/nginx.plist '
            result = self.sudo(cmd)

    @with_settings(warn_only=True)
    def stop(self):
        self.sudo('/etc/init.d/nginx stop')
