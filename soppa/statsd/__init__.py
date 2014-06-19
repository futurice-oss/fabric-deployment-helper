from soppa.contrib import *
from soppa.alias import mlcd
from soppa.deploy import DeployFrame

class StatsD(DeployFrame):
    needs=[
        'soppa.template',
        'soppa.supervisor',
    ]

    def pre(self):
        if not self.exists('{basepath}statsd'):
            with self.cd('{basepath}'):
                self.sudo('git clone https://github.com/etsy/statsd.git')

    def hook_pre_config(self):
        self.up('config/exampleConfig.js', '{basepath}statsd/')
        self.up('config/statsd_supervisor.conf', '{supervisor_conf_dir}')

    def stats(self):
        """ stats|counters|timers """
        self.sudo('echo "stats" | nc -w1 localhost 8126')

statsd_task, statsd = register(StatsD)
