import os, sys, datetime

from fabric.api import env

class DeployLog(object):
    def __init__(self, *args, **kwargs):
        self.data = {}
        meta = {
            'user': os.environ.get('USER', env.user),
            'date': datetime.datetime.now().isoformat(),
            'machine': os.popen('uname -a').read().strip(),}
        self.data['meta'] = meta
        self.data['hosts'] = {}
        self.actions = []

    def add(self, bucket, name, data):
        host = env.host_string
        hosts = self.data['hosts']
        hosts.setdefault(host, {})
        hosts[host].setdefault(name, {})
        hosts[host][name].setdefault(bucket, [])
        hosts[host][name][bucket].append(data)

    def add_action(self, action):
        self.actions.append(action)

    def get_action_instances(self):
        r = []
        for action in self.actions:
            instance = action[0]
            if any([isinstance(k, type(instance)) for k in r]):
                continue
            r.append(instance)
        return r
