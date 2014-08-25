from soppa.contrib import *

class Apt(Soppa):

    def update(self):
        key = 'apt.packages.updated.{0}'.format(env.host_string)
        if not env.CACHE.get(key):
            self.sudo('apt-get update -qq')
            env.CACHE[key] = True

    def install(self, packages, flags=''):
        if isinstance(packages, list):
            packages = ' '.join(list(set(packages)))
        self.sudo('apt-get install -q -y {0} {1}'.format(flags, packages))

    # TODO: base class methods for package-specific functionality
    def download(self, requirements, **kwargs):
        pass

    def sync(self, *args, **kwargs):
        pass
    #/TODO

