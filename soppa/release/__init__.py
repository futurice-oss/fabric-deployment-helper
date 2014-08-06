import os, hashlib
from soppa.contrib import *

class Release(Soppa):
    needs = ['soppa.operating']
    project=None
    deploy_user=os.environ.get('USER', 'root')
    deploy_group='www-data'
    deploy_os = 'debian'
    www_root='/srv/www/'
    basepath='{www_root}{project}/'
    project_root='{basepath}/www/'
    time = time.strftime('%Y%m%d%H%M%S')
    path = '{basepath}releases/{time}/'
    host = 'localhost'

    def ownership(self, owner=None):
        owner = owner or self.deploy_user
        self.sudo('chown -fR {owner} {basepath}', owner=owner)

    def dirs(self):
        self.sudo('mkdir -p {www_root}dist/')
        self.sudo('mkdir -p {basepath}{packages,releases/default/,media,static,dist,logs,config/vassals/,pids,cdn}')
        self.run('mkdir -p {path}')
        if not self.exists(self.project_root):
            with self.cd(self.basepath):
                self.run('ln -s {basepath}releases/default/ www.new; mv -T www.new www')

    def symlink_release(self):
        """ mv is atomic op on unix; allows seamless deploy """
        with self.cd(self.basepath):
            if self.operating.is_linux():
                self.run('ln -s {path} www.new; mv -T www.new www')
            else:
                self.run('rm -f www && ln -sf {path} www')

    def id(self, url):
        return hashlib.md5(url).hexdigest()

release_task, release = register(Release)
