from soppa.contrib import *

class CollectD(Soppa):
    from_source=False

collectd_task, collectd = register(CollectD)
