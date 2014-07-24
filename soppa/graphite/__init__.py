from soppa.contrib import *

from soppa.python import PythonDeploy

"""
Graphite by default installs to /opt/graphite/
Carbon configuration from:
https://github.com/graphite-project/carbon/tree/master/conf
"""
class Graphite(PythonDeploy):
    path='/opt/graphite/'
    web_path='{graphite_path}webapp/graphite/'
    host='localhost'
    carbon_path='/opt/graphite/'
    # internal
    required_settings=['host']
    packages={
        'pip': 'config/requirements.txt',
        'apt': ['libcairo2-dev','python-cairo','pkg-config','libpng3','libpng12-dev', 'libffi-dev'],
    }
    needs=PythonDeploy.needs+[
        'soppa.template',
        'soppa.nginx',
        'soppa.nodejs',
        'soppa.statsd',
    ]

    def hook_pre_config(self):
        self.sudo('mkdir -p {graphite_path}')
        self.sudo('chown -R {deploy_user} {graphite_path}')

        with self.cd('{graphite_path}conf/') as b, self.mlcd('config/') as a:
            self.up('carbon.conf', '{graphite_path}conf/carbon.conf')
            self.up('storage-schemas.conf', '{graphite_path}conf/storage-schemas.conf')
            if not self.exists('graphite.wsgi'):
                self.sudo('cp graphite.wsgi.example graphite.wsgi')
        with self.cd('{graphite_path}webapp/graphite/') as b, self.mlcd('config/') as a:
            self.up('local_settings.py', '{graphite_path}webapp/graphite/')
            self.sudo('chown {deploy_user} local_settings.py')

        self.up('graphite_supervisor.conf', '{supervisor.conf}')
        self.up('graphite_nginx.conf', '{nginx_dir}conf/sites-enabled/')

        args = 'syncdb --noinput'
        with self.virtualenv.activate(), self.cd('{web_path}'):
            self.sudo('python manage.py {args}'.format(args=args))

        # add system-wide python-cairo into virtualenv
        with self.virtualenv.activate():
            pkg_path = self.virtualenv.packages_path()
        cairo_path = self.pip.system_package_path('cairo')
        self.sudo("rm -f {0}cairo".format(pkg_path))
        self.sudo("ln -s {0} {1}".format(cairo_path.rstrip('/'), pkg_path.rstrip('/')))

        self.sudo('update-rc.d -f carbon remove')#TODO: generalize as factory.init_remove('carbon')

    def hook_post(self):
        self.nginx.restart()

graphite_task, graphite = register(Graphite)
