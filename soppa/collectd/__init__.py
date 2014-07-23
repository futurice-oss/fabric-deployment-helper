from soppa.contrib import *

class CollectD(Soppa):
    from_source=False
    packages={
        'apt': ['collectd'],
    }

collectd_task, collectd = register(CollectD)
