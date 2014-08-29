from soppa.contrib import *

class Redis(Soppa):

    def setup(self):
        if self.operating.is_linux():
            if self.linux.binary_exists('redis-server'):
                return
            self.sources()
            if not self.exists('/etc/apt/preferences.d/redis-server-dotdeb-pin-400'):
                with self.mlcd('config/'):
                    uptpl('redis-server-dotdeb-pin-400', '/etc/apt/preferences.d/')
            self.sudo('apt-get update')
            self.sudo('apt-get install redis-server')

    def sources(self):
        if self.operating.is_linux():
            self.file.set_setting('/etc/apt/sources.list', 'deb http://packages.dotdeb.org wheezy all')
            self.file.set_setting('/etc/apt/sources.list', 'deb-src http://packages.dotdeb.org wheezy all')
