from soppa.contrib import *

class StatsD(Soppa):

    def setup(self):
        self.virtualenv.setup()
        self.nodejs.setup()
        if not self.exists('{basepath}statsd'):
            with self.cd('{basepath}'):
                self.sudo('git clone https://github.com/etsy/statsd.git')
        self.up('exampleConfig.js', '{basepath}statsd/')

    def configure_supervisor(self):
        self.action('up', 'statsd_supervisor.conf', '{supervisor_conf_dir}', handler=['supervisor.restart'])

    def stats(self):
        """ stats|counters|timers """
        self.sudo('echo "stats" | nc -w1 localhost 8126')
