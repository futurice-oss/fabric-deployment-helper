from soppa.contrib import *

class Postgres(Soppa):
    path = '/etc/postgresql/9.1/main/'
    name = '{project}'
    user = ''
    password = ''
    needs = [
        'soppa.operating',
        'soppa.template',
    ]

    def setup(self):
        if self.operating.is_linux():
            self.install()
            self.create_database()

    def install(self):
        with settings(warn_only=True), self.hide('warnings'):
            self.sudo('pg_createcluster 9.1 main --start')

        self.sudo('chmod +x /etc/init.d/postgresql')
        self.sudo('update-rc.d postgresql defaults')

        self.action('up', 'pg_hba.conf', '{postgres_path}', handler=['postgres.restart'])

    def create_database(self):
        if not self.password or not self.user:
            raise Exception('Provide DATABASES settings')
        with settings(warn_only=True):
            self.sudo("su - postgres -c 'createuser {postgres_user} --no-superuser --no-createdb --no-createrole'")
            self.sudo("su - postgres -c 'createdb {postgres_name} -O {postgres_user}'")

postgres_task, postgres = register(Postgres)
