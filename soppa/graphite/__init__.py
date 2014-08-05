from soppa.contrib import *

class Graphite(Soppa):
    """
    Graphite by default installs to /opt/graphite/
    Carbon configuration from: https://github.com/graphite-project/carbon/tree/master/conf
    """
    path='/opt/graphite/'
    web_path='{graphite_path}webapp/graphite/'
    host='localhost'
    carbon_path='/opt/graphite/'
    required_settings=['host']
    needs=['soppa.template',
        'soppa.nginx',
        'soppa.nodejs',
        'soppa.statsd',

        'soppa.virtualenv',
        'soppa.supervisor',
        'soppa.redis',
        'soppa.pip',
        'soppa.remote',
    ]

    def go(self):
        self.sudo('mkdir -p {graphite_path}')
        self.sudo('chown -R {deploy_user} {graphite_path}')

        with self.cd('{graphite_path}conf/') as b, self.mlcd('config/') as a:
            self.up('carbon.conf', '{graphite_path}conf/carbon.conf')
            self.up('storage-schemas.conf', '{graphite_path}conf/storage-schemas.conf')
            if not self.exists('graphite.wsgi'):
                self.sudo('cp graphite.wsgi.example graphite.wsgi')
        with self.cd('{graphite_web_path}') as b, self.mlcd('config/') as a:
            self.up('local_settings.py', '{graphite_web_path}')
            self.sudo('chown {deploy_user} local_settings.py')

        self.supervisor.up('graphite_supervisor.conf', '{supervisor_conf_dir}')
        self.nginx.up('graphite_nginx.conf', '{nginx_dir}conf/sites-enabled/')

        with self.virtualenv.activate(), self.cd('{graphite_web_path}'):
            self.sudo('python manage.py syncdb --noinput')

        # add system-wide python-cairo into virtualenv
        with self.virtualenv.activate():
            pkg_path = self.virtualenv.packages_path()
        cairo_path = self.pip.system_package_path('cairo')
        self.sudo("rm -f {0}cairo".format(pkg_path))
        self.sudo("ln -s {0} {1}".format(cairo_path.rstrip('/'), pkg_path.rstrip('/')))

        self.sudo('update-rc.d -f carbon remove')#TODO: generalize as OS.init_remove('carbon')

graphite_task, graphite = register(Graphite)
