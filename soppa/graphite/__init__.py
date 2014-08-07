from soppa.contrib import *

class Graphite(Soppa):
    """
    Graphite by default installs to /opt/graphite/
    Carbon configuration from: https://github.com/graphite-project/carbon/tree/master/conf
    """
    path='/opt/graphite/'
    pathweb='{path}webapp/graphite/'
    host='localhost'
    carbon_path='{path}'
    required_settings=['host']
    need_web = 'soppa.nginx'
    needs=Soppa.needs+[
        'soppa.template',
        'soppa.nodejs',
        'soppa.statsd',

        'soppa.apt',
        'soppa.pip',

        'soppa.virtualenv',
        'soppa.supervisor',
        'soppa.redis',
        'soppa.remote',
    ]

    def go(self):
        self.sudo('mkdir -p {path}')
        self.sudo('chown -R {release.deploy_user} {path}')

        with self.cd('{path}conf/') as b, self.mlcd('config/') as a:
            self.up('carbon.conf', '{path}conf/carbon.conf')
            self.up('storage-schemas.conf', '{path}conf/storage-schemas.conf')
            if not self.exists('graphite.wsgi'):
                self.sudo('cp graphite.wsgi.example graphite.wsgi')
        with self.cd('{pathweb}') as b, self.mlcd('config/') as a:
            self.up('local_settings.py', '{pathweb}')
            self.sudo('chown {release.deploy_user} local_settings.py')

        self.supervisor.up('graphite_supervisor.conf', '{supervisor_conf_dir}')
        self.web.up('graphite_nginx.conf', '{web.conf_dir}')

        with self.virtualenv.activate(), self.cd('{pathweb}'):
            self.sudo('python manage.py syncdb --noinput')

        # add system-wide python-cairo into virtualenv
        with self.virtualenv.activate():
            pkg_path = self.virtualenv.packages_path()
        cairo_path = self.pip.system_package_path('cairo')
        self.sudo("rm -f {0}cairo".format(pkg_path))
        self.sudo("ln -s {0} {1}".format(cairo_path.rstrip('/'), pkg_path.rstrip('/')))

        self.sudo('update-rc.d -f carbon remove')#TODO: generalize as OS.init_remove('carbon')

graphite_task, graphite = register(Graphite)
