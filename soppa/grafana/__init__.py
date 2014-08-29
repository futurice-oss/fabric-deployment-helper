from soppa.contrib import *

class Grafana(Soppa):
    url = 'http://grafanarel.s3.amazonaws.com/grafana-1.5.3.tar.gz'
    web_host = 'grafana.dev'
    project = 'grafana'

    def setup(self):
        # self.package.get_file(url, dest)
        # - normal file download, ensures dest= exists
        # self.package.get_file(url, dest)
        # - handle dirs, ownership, symlink ... according to chosen need_release
        self.package.file_as_release(self.url, dest=self.path)

        self.up('config.js', '{path}')

    def configure_nginx(self):
        self.action('up', 'grafana_nginx.conf', '{nginx_conf_dir}', handler=['nginx.restart'])
