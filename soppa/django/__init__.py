from soppa.contrib import *
from soppa.internal.mixins import DirectoryMixin

class Django(Soppa, DirectoryMixin):
    settings = '{project}.settings.prod'

    def setup(self):
        self.virtualenv.setup()
        self.nodejs.setup()

    def hook_post(self):
        self.set_dsm(self.settings)

        with settings(warn_only=True):# assumes assetgen
            self.prepare_assets()

        with settings(warn_only=True):# assumes settings.DATABASES
            self.manage('syncdb --noinput')

        with settings(warn_only=True):
            self.manage('migrate --noinput')# assumes South/django 1.7

        self.check_dsm()

    def set_dsm(self, dsm):
        self.file.set_setting(
                self.fmt('{virtualenv_path}bin/activate'),
                self.fmt('export DJANGO_SETTINGS_MODULE={dsm}', dsm=dsm))

    def check_dsm(self):
        with self.virtualenv.activate(), self.cd(self.path):
            result = self.sudo('env|grep DJANGO_SETTINGS_MODULE')
            assert self.fmt(self.settings) in result

    def reset_and_sync(self):
        self.manage('reset_db --router=default --noinput')
        self.manage('syncdb --noinput')

    def prepare_assets(self):
        with self.virtualenv.activate(), self.cd(self.path):
            self.sudo('assetgen --profile prod assetgen.yaml --force && cp -r {path}static/* {basepath}static/')
        self.manage('collectstatic --noinput')

    def manage(self, args, standalone=False):
        with self.virtualenv.activate(), self.cd(self.path):
            return self.sudo('python manage.py {args}'.format(args=args))

    def admin(self, args, standalone=False):
        with self.virtualenv.activate(), self.cd(self.path):
            return self.run('django-admin.py {args}'.format(args=args))

    def database_env(self, django_settings=None):
        django_settings = self.fmt(django_settings or self.settings)
        rs = {}
        try:
            dsm = import_string(django_settings)
        except ImportError, e:
            print "DJANGO_SETTINGS_MODULE not found: {0}".format(e)
            return rs
        db = dsm.DATABASES['default']
        rs = dict(
            engine=db['ENGINE'],
            name=db['NAME'],
            user=db['USER'],
            password=db['PASSWORD'],
            options=db.get('OPTIONS', {}),
        )
        return rs
