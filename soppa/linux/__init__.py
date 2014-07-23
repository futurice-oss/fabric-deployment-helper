from soppa.contrib import *

class Linux(Soppa):
    needs=[
        'soppa.file',
        'soppa.remote',
    ]

    def swap_on(self):
        self.remote.run_cmd('soppa.linux.swap')

    def hello(self, args=[]):
        self.sudo('echo "hello world" {0}'.format(args))

    def hello_remote(self, args=[]):
        self.remote.run_cmd('soppa.linux.hello')

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
