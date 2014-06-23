from soppa.contrib import *

class Postgres(Soppa):
    path='/etc/postgresql/9.1/main/'
    name='{project}'
    user=''
    password=''
    packages={
        'apt': [
            'postgresql-9.1',
            'libpq-dev'],
    }
    needs=[
        'soppa.operating',
        'soppa.template',
    ]

    def setup(self):
        if self.operating.is_linux():
            self.install()

    def install(self):
        with settings(warn_only=True):
            self.sudo('pg_createcluster 9.1 main --start')

        self.up('config/pg_hba.conf', '{path}')
        # TODO: if settings modified, need to restart server

        self.sudo('chmod +x /etc/init.d/postgresql')
        self.sudo('update-rc.d postgresql defaults')

    def rights(self):
        # TODO: postgres.settings() dbname,dbuser not used at all
        if not self.password or not self.user:
            raise Exception('Provide DATABASES settings')
        with settings(warn_only=True):
            self.sudo("su - postgres -c 'createuser {user} --no-superuser --no-createdb --no-createrole'")
            self.sudo("su - postgres -c 'createdb {name} -O {user}'")

postgres_task, postgres = register(Postgres)
