from soppa.contrib import *

from soppa.apt import *
from soppa.apache import *
from soppa.celery import *
from soppa.collectd import *
from soppa.django import *
from soppa.dnsmasq import *
from soppa.elasticsearch import *
from soppa.firewall import *
from soppa.file import *
from soppa.grafana import *
from soppa.graphite import *
from soppa.java import *
from soppa.linux import *
from soppa.mysql import *
from soppa.nginx import *
from soppa.nodejs import *
from soppa.pip import *
from soppa.package import *
from soppa.postgres import *
from soppa.redis import *
from soppa.remote import *
from soppa.rsync import *
from soppa.sentry import *
from soppa.statsd import *
from soppa.supervisor import *
from soppa.template import *
from soppa.uwsgi import *
from soppa.vagrant import *
from soppa.virtualenv import *

def list_imports(module):
    d = here(fn=import_string(module).__file__)
    return [o for o in os.listdir(d) if os.path.isdir(os.path.join(d,o))]

def print_imports(module):
    for k in list_imports(module):
        print "from soppa.{} import *".format(k)
