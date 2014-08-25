from soppa.contrib import *

class Apache(Soppa):
    restart_command='/etc/init.d/apache2 restart'
    dir='/etc/apache2/'
    __doc__='conf|restart'
    pkg={'apt': ['apache2-mpm-prefork']}

    def restart():
        self.sudo('{apache_restart_command}', pty=False)

    def setup():
        if not linux.binary_exists('apache2'):
            self.sudo('apt-get install apache2-mpm-prefork')
        self.sudo('a2enmod proxy rewrite headers proxy_http')
