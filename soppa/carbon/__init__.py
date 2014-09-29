from soppa.contrib import *

class Carbon(Soppa):
    path = '/opt/graphite/'

    def setup(self):
        self.sudo('mkdir -p {path}')
        self.sudo('chown -R {user} {path}')

        with self.cd('{path}conf/'):
            self.up('carbon.conf', '{path}conf/carbon.conf')
            self.up('storage-schemas.conf', '{path}conf/storage-schemas.conf')

        self.sudo('update-rc.d -f carbon remove')#TODO: generalize as OS.init_remove('carbon')
