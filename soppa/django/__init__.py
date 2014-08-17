from soppa.contrib import *

class Django(Soppa):
    settings='{project}.settings.prod'
    needs=['soppa.file',
        'soppa.uwsgi',
        'soppa.nginx',
        'soppa.mysql',
        'soppa.nodejs',
        'soppa.template',

        'soppa.virtualenv',
        'soppa.supervisor',
        'soppa.redis',
        'soppa.pip',
        'soppa.remote',

        'soppa.operating',
        'soppa.apt',
    ]
    need_web = 'soppa.nginx'
    need_db = 'soppa.mysql'
    need_wsgi = 'soppa.uwsgi'

    def hook_post(self):
        self.set_dsm(self.settings)

        with settings(warn_only=True):# assumes assetgen
            self.prepare_assets()

        with settings(warn_only=True):# assumes settings.DATABASES
            self.manage('syncdb --noinput')

        with settings(warn_only=True):
            self.manage('migrate --noinput')# assumes South/django 1.7

        self.check()

    def set_dsm(self, dsm):
        self.file.set_setting(
                self.fmt('{virtualenv_path}bin/activate'),
                self.fmt('export DJANGO_SETTINGS_MODULE={dsm}', dsm=dsm))

    def check(self):
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

django_task, django = register(Django)
