from soppa.contrib import *

class Grafana(Soppa):
    url='http://grafanarel.s3.amazonaws.com/grafana-1.5.3.tar.gz'
    needs=[
        'soppa.file',
        'soppa.operating',

        'soppa.package',
        'soppa.template',

        'soppa.release',
    ]
    need_web = 'soppa.nginx'
    web_host = 'grafana.dev'
    release_project = 'grafana'
    release_path = '{release.basepath}releases/{release.time}/'

    def go(self):
        print "GRAFANA SETUP"
        self.release.dirs()
        self.package.file_as_release(self.url, dest=self.release_path)
        # self.release.get_url
        # self.release.tar.unpack()
        self.release.ownership()
        self.release.symlink()

        self.web.up('grafana_nginx.conf', '{nginx_dir}conf/sites-enabled/')
        self.up('config.js', '{project_root}')

grafana_task, grafana = register(Grafana)
