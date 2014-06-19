from soppa.contrib import *

from soppa.python import PythonDeploy

"""
Graphite by default installs to /opt/graphite/
Carbon configuration from:
https://github.com/graphite-project/carbon/tree/master/conf
"""
class Graphite(PythonDeploy):
    graphite_dir='/opt/graphite/'
    graphite_web_dir='{graphite_dir}webapp/graphite/'
    graphite_servername='localhost'
    graphite_carbon_dir='/opt/graphite/'
    # internal
    required_settings=['graphite_servername']
    packages={
        'pip': 'config/requirements.txt',
        'apt': ['libcairo2-dev','python-cairo','pkg-config','libpng3','libpng12-dev', 'libffi-dev'],
    }
    needs=['soppa.virtualenv',
        'soppa.template',
        'soppa.pip',
        'soppa.nginx',
        'soppa.supervisor',
        'soppa.nodejs',
        'soppa.statsd',
        'soppa.operating',#TODO:inherit Deploy
        'soppa.redis',#TODO:inherit Deploy
    ]

    def hook_pre_config(self):
        self.sudo('mkdir -p {graphite_dir}')
        self.sudo('chown -R {deploy_user} {graphite_dir}')

        with self.cd('{graphite_dir}conf/') as b, self.mlcd('config/') as a:
            self.up('config/carbon.conf', '{graphite_dir}conf/carbon.conf')
            self.up('config/storage-schemas.conf', '{graphite_dir}conf/storage-schemas.conf')
            if not self.exists('graphite.wsgi'):
                self.sudo('cp graphite.wsgi.example graphite.wsgi')
        with self.cd('{graphite_dir}webapp/graphite/') as b, self.mlcd('config/') as a:
            self.up('config/local_settings.py', '{graphite_dir}webapp/graphite/')
            self.sudo('chown {deploy_user} local_settings.py')

        self.up('config/graphite_supervisor.conf', '{supervisor_conf_dir}')
        self.up('config/graphite_nginx.conf', '{nginx_dir}conf/sites-enabled/')

        args = 'syncdb --noinput'
        with self.virtualenv.activate() as a, self.cd('{graphite_web_dir}') as b:
            self.sudo('python manage.py {args}'.format(args=args))

        # add system-wide python-cairo into virtualenv
        with self.virtualenv.activate():
            pkg_path = self.virtualenv.packages_path()
        cairo_path = self.pip.system_package_path('cairo')
        self.sudo("rm -f {0}cairo".format(pkg_path))
        self.sudo("ln -s {0} {1}".format(cairo_path.rstrip('/'), pkg_path.rstrip('/')))

        self.sudo('update-rc.d -f carbon remove')#TODO: generalize as factory.init_remove('carbon')

    def hook_pre(self):
        # Q: run .setup() for everythin in needs?
        self.nginx.setup()
        self.nodejs.setup()
        self.statsd.setup()

    def hook_post(self):
        self.nginx.restart()

graphite_task, graphite = register(Graphite)
