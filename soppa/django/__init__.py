from soppa.contrib import *

from soppa.local import aslocal, osx
from soppa.alias import mlcd
from soppa.remote import run_cmd, setup_runner

from soppa.python import PythonDeploy

class Django(PythonDeploy):
    settings='{project}.settings.prod'
    needs=[
        'soppa.virtualenv',
        'soppa.file',
        'soppa.uwsgi',
        'soppa.nginx',
        'soppa.redis',
        'soppa.mysql',
        'soppa.supervisor',
        'soppa.nodejs',
        'soppa.pip',
        'soppa.template',

        'soppa.operating',
        'soppa.apt',
    ]
    packages={
        'pip': ['Django==1.6'],
    }

    def hook_post_start(self):
        self.install_all_packages()

    def hook_pre(self):
        self.database_env()

    def hook_post(self):
        with settings(warn_only=True):# assumes assetgen
            self.prepare_assets()

        with settings(warn_only=True):# assumes settings.DATABASES
            self.manage('syncdb --noinput')

        with settings(warn_only=True):
            self.manage('migrate --noinput')# assumes South/django 1.7

    def hook_end(self):
        self.check()
        self.nginx.restart()
        self.supervisor.restart()

    def hook_post_config(self):
        self.set_dsm(self.env.django_settings)

    def set_dsm(self, dsm):
        self.file.set_setting(
                self.fmt('{virtualenv_dir}bin/activate'),
                self.fmt('export DJANGO_SETTINGS_MODULE={dsm}', dsm=dsm))

    def check(self):
        with self.virtualenv.activate() as a, self.cd(self.env.usedir) as b:
            result = self.sudo('env|grep DJANGO_SETTINGS_MODULE')
            assert self.env.django_settings in result

    def reset_and_sync(self):
        self.manage('reset_db --router=default --noinput')
        self.manage('syncdb --noinput')

    def prepare_assets(self):
        with self.virtualenv.activate() as a, self.cd(self.env.usedir) as b:
            self.sudo('assetgen --profile prod assetgen.yaml --force && cp -r {usedir}static/* {basepath}static/')
        self.manage('collectstatic --noinput')

    def manage(self, args, standalone=False):
        with self.virtualenv.activate() as a, self.cd(self.env.usedir) as b:
            return self.sudo('python manage.py {args}'.format(args=args))

    def admin(self, args, standalone=False):
        with self.virtualenv.activate() as a, self.cd(self.env.usedir) as b:
            return self.run('django-admin.py {args}'.format(args=args))

    def database_env(self, django_settings=None):
        django_settings = self.fmt(django_settings or self.env.django_settings)
        rs = {}
        try:
            dsm = import_string(django_settings)
        except ImportError, e:
            print "DJANGO_SETTINGS_MODULE not found: {0}".format(e)
            return rs
        db = dsm.DATABASES['default']
        rs=dict(
            dbengine=db['ENGINE'],
            dbname=db['NAME'],
            dbuser=db['USER'],
            dbpass=db['PASSWORD'],
            dboptions=db.get('OPTIONS', {}),
        )
        return rs

django_task, django = register(Django)
