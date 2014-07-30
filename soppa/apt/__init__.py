from soppa.contrib import *

env.apt_updated = {}

class Apt(Soppa):

    def packages_updated(self):
        return env.apt_updated.setdefault(env.host_string, False)

    def set_packages_updated(self):
        env.apt_updated.setdefault(env.host_string, True)

    def update(self):
        if self.packages_updated():
            return
        self.sudo('apt-get update -qq')
        self.set_packages_updated()

    def install(self, packages, flags=''):
        if isinstance(packages, list):
            packages = ' '.join(list(set(packages)))
        self.sudo('apt-get install -q -y {0} {1}'.format(flags, packages))

apt_task, apt = register(Apt)
