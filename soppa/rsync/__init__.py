from soppa.contrib import *


class Rsync(Soppa):
    deploy_group = 'www-data'

    def rsync_target(self):
        fmt = self.fmt('{env.user}@{host}:')
        if self.env.use_ssh_config:#TODO:should never need to self.env
            fmt = self.fmt('{env.user}@{env.host_string}:')
        if self.local_deployment:
            fmt = ''
        return fmt

    def rsync_up(self, args, source, target):
        self.sudo('mkdir -p {0}'.format(target))
        self.sudo('chgrp {0} {1}'.format(self.deploy_group, target))
        self.sudo('chmod -R g+w {0}'.format(target))
        self.sudo('chown -R {} {}'.format(self.user, target))
        if hasattr(self, 'key_filename'):
            args += " -e 'ssh -i {0}'".format(self.key_filename[0])
        self.local('rsync -r {args} {source} {rsync_target}{target}',
            args=args,
            source=source,
            target=target,
            rsync_target=self.rsync_target(),)
