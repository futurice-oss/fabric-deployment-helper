from soppa.contrib import *

class Graphite(Soppa):
    """
    Graphite by default installs to /opt/graphite/
    Carbon configuration from: https://github.com/graphite-project/carbon/tree/master/conf
    """
    path = '/opt/graphite/'
    pathweb = '{path}webapp/graphite/'
    host = 'localhost'
    carbon_path = '{path}'

    def setup(self):
        self.virtualenv.setup()

        self.sudo('mkdir -p {path}')
        self.sudo('chown -R {user} {path}')

        with self.cd('{path}conf/'):
            self.up('carbon.conf', '{path}conf/carbon.conf')
            self.up('storage-schemas.conf', '{path}conf/storage-schemas.conf')
            if not self.exists('graphite.wsgi'):
                self.sudo('cp graphite.wsgi.example graphite.wsgi')
        self.up('local_settings.py', '{pathweb}')
        self.sudo('chown {user} {pathweb}local_settings.py')

        with self.virtualenv.activate(), self.cd('{pathweb}'):
            self.sudo('python manage.py syncdb --noinput')

        # add system-wide python-cairo into virtualenv
        with self.virtualenv.activate():
            pkg_path = self.virtualenv.packages_path()
        cairo_path = self.pip.system_package_path('cairo')
        self.sudo("rm -f {0}cairo".format(pkg_path))
        self.sudo("ln -s {0} {1}".format(cairo_path.rstrip('/'), pkg_path.rstrip('/')))

        self.sudo('update-rc.d -f carbon remove')#TODO: generalize as OS.init_remove('carbon')

    def configure_nginx(self):
        self.action('up', 'graphite_nginx.conf', '{nginx_conf_dir}', handler=['nginx.restart'])

    def configure_supervisor(self):
        self.action('up', 'graphite_supervisor.conf', '{supervisor_conf_dir}', handler=['supervisor.restart'])
