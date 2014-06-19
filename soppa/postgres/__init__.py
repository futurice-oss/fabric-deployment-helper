from soppa.contrib import *

class Postgres(Soppa):
    postgres_conf_dir='/etc/postgresql/9.1/main/'
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

        self.up('config/pg_hba.conf', '{postgres_conf_dir}')
        # TODO: if settings modified, need to restart server

        self.sudo('chmod +x /etc/init.d/postgresql')
        self.sudo('update-rc.d postgresql defaults')

    def rights(self):
        # TODO: postgres.settings() dbname,dbuser not used at all
        if not env.dbpass or not env.dbuser:
            raise Exception('Provide DATABASES settings')
        with settings(warn_only=True):
            self.sudo("su - postgres -c 'createuser {dbuser} --no-superuser --no-createdb --no-createrole'")
            self.sudo("su - postgres -c 'createdb {dbname} -O {dbuser}'")

postgres_task, postgres = register(Postgres)
