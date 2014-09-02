from soppa.contrib import *

class Apache(Soppa):
    restart_command = '/etc/init.d/apache2 restart'
    path = '/etc/apache2/'

    def restart():
        self.sudo('{apache_restart_command}', pty=False)

    def setup():
        self.sudo('a2enmod proxy rewrite headers proxy_http')
