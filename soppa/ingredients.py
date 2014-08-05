from soppa.contrib import *

from .apt import *
from .apache import *
from .celery import *
from .collectd import *
from .django import *
from .dnsmasq import *
from .elasticsearch import *
from .firewall import *
from .file import *
from .grafana import *
from .graphite import *
from .java import *
from .linux import *
from .mysql import *
from .nginx import *
from .nodejs import *
from .pip import *
from .package import *
from .postgres import *
from .redis import *
from .remote import *
from .rsync import *
from .sentry import *
from .statsd import *
from .supervisor import *
from .template import *
from .uwsgi import *
from .vagrant import *
from .virtualenv import *
from .xs import *

def print_imports(module):
    d = here(fn=import_string(module).__file__)
    installed_packages = [o for o in os.listdir(d) if os.path.isdir(os.path.join(d,o))]
    for k in installed_packages:
        print "from {0} import *".format(k)
