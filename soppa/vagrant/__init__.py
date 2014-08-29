import time

from soppa.contrib import *

class Vagrant(Soppa):
    def guest_ip(self):
        return self.sudo("""ifconfig -a eth1|grep "inet addr"|awk '{gsub("addr:","",$2); print $2}'""")

    def enable_host(self, name):
        """
        Romain forwarding for local development with Vagrant.
        domain (host) -> domain (guest)
        """
        from soppa.local import aslocal
        self.guest_ip = self.guest_ip()
        self.guest_host_name = name
        # Host (remote) change
        self.file.set_setting('/etc/hosts', '{0} {1}'.format('127.0.0.1', self.guest_host_name))
        # local change
        aslocal()
        self.file.set_setting('/etc/hosts', '{0} {1}'.format(self.guest_ip, name))
