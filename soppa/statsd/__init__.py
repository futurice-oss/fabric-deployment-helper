from soppa.contrib import *
from soppa.deploy import DeployFrame

class StatsD(DeployFrame):
    needs=DeployFrame.needs+[
        'soppa.template',
        'soppa.supervisor',
        'soppa.virtualenv',
        'soppa.nodejs',
    ]

    def go(self):
        if not self.exists('{basepath}statsd'):
            with self.cd('{basepath}'):
                self.sudo('git clone https://github.com/etsy/statsd.git')
        self.up('exampleConfig.js', '{basepath}statsd/')
        self.up('statsd_supervisor.conf', '{supervisor.conf}')

    def stats(self):
        """ stats|counters|timers """
        self.sudo('echo "stats" | nc -w1 localhost 8126')

statsd_task, statsd = register(StatsD)
