import os, sys, datetime
from soppa import *

class DeployLog(object):
    def __init__(self, *args, **kwargs):
        self.data = {}
        meta = {
            'user': os.environ.get('USER', env.user),
            'date': datetime.datetime.now().isoformat(),
            'machine': os.popen('uname -a').read().strip(),}
        self.data['meta'] = meta
        self.data['hosts'] = {}

    def add(self, bucket, need, data):
        host = env.host_string
        need_name = need.get_name()
        hosts = self.data['hosts']
        hosts.setdefault(host, {})
        hosts[host].setdefault(need_name, {})
        hosts[host][need_name].setdefault(bucket, [])
        hosts[host][need_name][bucket].append(data)
