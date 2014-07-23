import os

from soppa.contrib import *
from soppa.deploy import DeployFrame

class Grafana(DeployFrame):
    url='http://grafanarel.s3.amazonaws.com/grafana-1.5.3.tar.gz'
    servername='grafana.dev'
    needs=DeployFrame.needs+[
        'soppa.package',
        'soppa.template',
        'soppa.nginx',
    ]

    def hook_start(self):
        self.package.url = self.url

    def hook_post(self):
        # needs=[] have their own env
        self.up('config/grafana_nginx.conf', '{nginx_dir}conf/sites-enabled/')
        self.up('config/config.js', '{project_root}')

grafana_task, grafana = register(Grafana)
