from soppa.contrib import *


class Rsync(Soppa):
    rsync_up_command='rsync -r {args} {source} {rsync_target}{target}'

    def rsync_target(self):
        fmt = self.fmt('{user}@{host}:')
        if self.use_ssh_config:
            fmt = self.fmt('{user}@{host_string}:')
        if self.local_deployment:
            fmt = ''
        return fmt

    def rsync_up(self, args, source, target):
        self.sudo('mkdir -p {0}'.format(target))
        self.sudo('chgrp {0} {1}'.format(self.deploy_group, target))
        self.sudo('chmod -R g+w {0}'.format(target))
        if self.key_filename:
            args += " -e 'ssh -i {0}'".format(self.key_filename[0])
        self.local(self.rsync_up_command.format(
            args=args,
            source=source,
            target=target,
            rsync_target=self.rsync_target(),))

rsync_task, rsync = register(Rsync)
