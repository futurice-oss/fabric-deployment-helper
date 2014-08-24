from soppa.contrib import *

class Grafana(Soppa):
    url = 'http://grafanarel.s3.amazonaws.com/grafana-1.5.3.tar.gz'
    needs=[
        'soppa.file',
        'soppa.operating',

        'soppa.package',
        'soppa.template',
    ]
    need_web = 'soppa.nginx'
    web_host = 'grafana.dev'
    project = 'grafana'

    def setup(self):
        # self.package.get_file(url, dest)
        # - normal file download, ensures dest= exists
        # self.package.get_file(url, dest)
        # - handle dirs, ownership, symlink ... according to chosen need_release
        self.dirs()
        self.package.file_as_release(self.url, dest=self.path)
        self.ownership()
        self.symlink()

        if self.has_need('nginx'):
            self.action('up', 'grafana_nginx.conf', '{nginx_conf_dir}', handler=['nginx.restart'])
        self.up('config.js', '{path}')

grafana_task, grafana = register(Grafana)
