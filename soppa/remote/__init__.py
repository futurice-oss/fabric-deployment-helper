import json, time, os, copy

from soppa.contrib import *

class SilentEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError, e:
            return None

class Remote(Soppa):
    runner_path = '{root.release.basepath}releases/runner.py'
    needs=Soppa.needs+[
        'soppa.file',
        'soppa.virtualenv',
        'soppa.template',
    ]

    def to_json(self, data, cls=None):
        return json.dumps(data, encoding='utf-8', cls=cls, ensure_ascii=False, separators=(',',':'))

    def run_cmd(self, cmd):#TODO:rename as remote_cmd
        self.sync_local_fabric_env()
        with self.virtualenv.activate(), self.cd(self.root.release.release_path):
            if env.local_deployment:
                fn = self.file.import_string(cmd)
                fn()
            else:
                self.sudo('python {runner_path} --cmd={cmd} --filename={sync_filename}')
        # TODO: cleanup created sync.json that remains

    def setup(self):
        self.up('runner.py', self.runner_path)
        self.sudo('chmod +x {0}'.format(self.runner_path))

    def sync_local_fabric_env(self):
        """ Sync current fabric.env when running commands on a remote server
        - create dist/runner.py for executing remote commands
        """
        env.sync_filename = '/tmp/{0}_env.txt'.format(time.time())
        env_copy = self.env
        env_copy.use_ssh_config = False
        env_copy.host = False
        env_copy.host_string = False
        env_copy.local_deployment = True
        # TODO: add context from each need to repopulate
        with self.file.tmpfile(self.to_json(env_copy, cls=SilentEncoder)) as f:
            self.up(f.name, env.sync_filename)

    def run_cmd_alone(self, cmd):
        """ Run commands defined in local fabfile, on remote server, by copying fabfile and executing command there """
        self.put('fabfile.py', '/tmp/')

        with self.cd('/tmp'):
            self.run('python -c "from fabfile import *; execute({cmd});"'.format(cmd=cmd))

remote_task, remote = register(Remote)
