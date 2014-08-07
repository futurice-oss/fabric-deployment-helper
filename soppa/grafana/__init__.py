from soppa.contrib import *

class Grafana(Soppa):
    url = 'http://grafanarel.s3.amazonaws.com/grafana-1.5.3.tar.gz'
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

    def go(self):
        # self.package.get_file(url, dest)
        # - normal file download, ensures dest= exists
        # self.release.package.get_file(url, dest)
        # - handle dirs, ownership, symlink ... according to chosen need_release
        self.release.dirs()
        self.package.file_as_release(self.url, dest=self.release.path)
        self.release.ownership()
        self.release.symlink()

        self.web.up('grafana_nginx.conf', '{web.conf_dir}')
        self.up('config.js', '{release.project_root}')

grafana_task, grafana = register(Grafana)
