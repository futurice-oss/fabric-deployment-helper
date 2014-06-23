import time, getpass

from soppa.contrib import *
from soppa.local import aslocal

class DeployFrame(Soppa):
    packages={}
    needs=[
        'soppa.file',
    ]

    def setup(self):
        self.hook_start()
        self.start()
        self.hook_post_start()

        self.setup_needs()

        self.hook_pre()
        self.pre()

        self.hook_pre_config()
        self.configure()
        self.hook_post_config()

        self.post()
        self.hook_post()
        with settings(warn_only=True):
            self.restart_all()

        self.end()
        self.hook_end()

    def setup_needs(self):
        instances = []
        for key in self.needs:
            name = key.split('.')[-1]
            instance = getattr(self, name)
            getattr(instance, 'setup')()

    def pre(self):
        pass

    def start(self):
        pass

    def configure(self):
        pass

    def post(self):
        pass

    def end(self):
        pass

    def restart_all(self):
        pass

    ## HOOKS
    
    def hook_post_start(self):
        pass

    def hook_pre(self):
        pass

    def hook_post(self):
        pass

    def hook_pre_config(self):
        pass

    def hook_post_config(self):
        pass

    def hook_start(self):
        pass

    def hook_end(self):
        pass

    ## END HOOKS

    def ownership(self):
        self.sudo('chown -fR {owner} {basepath}')

    def dirs(self):
        self.sudo('mkdir -p {www_root}dist/')
        self.sudo('mkdir -p {basepath}{packages,releases,media,static,dist,logs,config/vassals/,pids,cdn}')

    def ask_sudo_password(self, capture=False):
        print "SUDO PASSWORD PROMPT (leave blank, if none needed)"
        if not env.get('password', None):
            env.password = getpass.getpass('Sudo password ({0}):'.format(env.host))

    def umask(self, value='002'):
        return self.prefix('umask {value}'.format(value=value))

    def upload_tar(self):
        self.put('{deploy_tarball}', '{basepath}packages/')
        with self.cd(self.basepath):
            self.run('mkdir -p releases/{release}')
            self.run('tar zxf packages/{release}.tar.gz -C releases/{release}')
        self.local('rm {deploy_tarball}')

    def tar_from_git(self):
        self.local('git archive --format=tar {branch} | gzip > {deploy_tarball}')

    def symlink_exists(self):
        return self.exists('{release_symlink_path}')

    def symlink_release(self, path=None):
        """ mv is atomic op on unix; allows seamless deploy """
        with self.cd(env.basepath):
            if self.operating.is_linux():
                self.run('ln -s {release_symlink_path} www.new; mv -T www.new www')
            else:
                self.run('rm -f www && ln -sf {release_symlink_path} www')

    def password_prompt(self):
        if not env.password:
            if self.whoami() == 'root':
                return
            ask_sudo_password(capture=False)

    def whoami(self):
        return self.sudo('whoami')

