from soppa.contrib import *

class Grafana(Soppa):
    url='http://grafanarel.s3.amazonaws.com/grafana-1.5.3.tar.gz'
    servername='grafana.dev'
    needs=[
        'soppa.file',
        'soppa.operating',

        'soppa.package',
        'soppa.template',
        'soppa.nginx',
    ]

    def go(self):
        self.package.file_as_release(self.url)
        self.nginx.up('grafana_nginx.conf', '{nginx_dir}conf/sites-enabled/')
        self.up('config.js', '{project_root}')

grafana_task, grafana = register(Grafana)
