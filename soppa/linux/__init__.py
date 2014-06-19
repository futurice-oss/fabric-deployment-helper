from soppa.contrib import *

from soppa.remote import run_cmd

class Linux(Soppa):
    needs=[
        'soppa.file',
    ]

    def swap_on(self):
        run_cmd('soppa.linux.swap')

    def swap(self):
        if not self.exists('/swapfile'):
            self.sudo('mkswap /swapfile')
            self.sudo('swapon /swapfile')
            self.sudo('chown root:root /swapfile')
            self.sudo('chmod 0600 /swapfile')
        self.file.set_setting('/etc/fstab', '/swapfile       none    swap    sw,noatime,nosuid      0       0')
        self.file.set_setting('/etc/sysctl.conf', 'vm.swappiness=0')

    def swap_status(self):
        self.sudo('swapon -s')

    def modify_hosts_vm(self):
        self.file.set_setting('/etc/hosts', '127.0.0.1 %(hostname)s www.%(hostname)s')

    def running(self, cmd='', echo=False):
        """ check if process is running """
        with self.hide('output','warnings'), settings(warn_only=True):
            result = self.sudo(cmd)
        if echo:
            print str(result.succeeded)
        return result.succeeded

    def binary_exists(self, name):
        with self.hide('output','warnings'), settings(warn_only=True):
            result = self.sudo("command -v "+name+" >/dev/null 2>&1 || { echo >&2 'Not installed'; exit 1; }")
        return result.succeeded

linux_task, linux = register(Linux)
