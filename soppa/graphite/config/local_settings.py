SECRET_KEY = '/~Xz2rpHMcEW/hqfV{Dsl{l^qI?=%81sWwb.$BqQrfq,x*z!k9'
ALLOWED_HOSTS = ['*']
TIME_ZONE = 'Europe/Helsinki'

# If using RRD files and rrdcached, set to the address or socket of the daemon
#FLUSHRRDCACHED = 'unix:/var/run/rrdcached.sock'

MEMCACHE_HOSTS = ['127.0.0.1:11211']
DEFAULT_CACHE_DURATION = 60


#####################################
# Email Configuration #
#####################################
# This is used for emailing rendered Graphs
# Default backend is SMTP
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_HOST = 'localhost'
#EMAIL_PORT = 25
#EMAIL_HOST_USER = ''
#EMAIL_HOST_PASSWORD = ''
#EMAIL_USE_TLS = False
# To drop emails on the floor, enable the Dummy backend:
#EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'


##########################
# Database Configuration #
##########################
# By default sqlite is used. If you cluster multiple webapps you will need
# to setup an external database (such as MySQL) and configure all of the webapp
# instances to use the same database. Note that this database is only used to store
# Django models such as saved graphs, dashboards, user preferences, etc.
# Metric data is not stored here.
#
# DO NOT FORGET TO RUN 'manage.py syncdb' AFTER SETTING UP A NEW DATABASE
#
# The following built-in database engines are available:
#  django.db.backends.postgresql          # Removed in Django 1.4
#  django.db.backends.postgresql_psycopg2
#  django.db.backends.mysql
#  django.db.backends.sqlite3
#  django.db.backends.oracle
#
# The default is 'django.db.backends.sqlite3' with file 'graphite.db'
# located in STORAGE_DIR
#
#DATABASES = {
#    'default': {
#        'NAME': '/opt/graphite/storage/graphite.db',
#        'ENGINE': 'django.db.backends.sqlite3',
#        'USER': '',
#        'PASSWORD': '',
#        'HOST': '',
#        'PORT': ''
#    }
#}
#


#########################
# Cluster Configuration #
#########################
# (To avoid excessive DNS lookups you want to stick to using IP addresses only in this entire section)
#
# This should list the IP address (and optionally port) of the webapp on each
# remote server in the cluster. These servers must each have local access to
# metric data. Note that the first server to return a match for a query will be
# used.
#CLUSTER_SERVERS = ["10.0.2.2:80", "10.0.2.3:80"]

## These are timeout values (in seconds) for requests to remote webapps
#REMOTE_STORE_FETCH_TIMEOUT = 6   # Timeout to fetch series data
#REMOTE_STORE_FIND_TIMEOUT = 2.5  # Timeout for metric find requests
#REMOTE_STORE_RETRY_DELAY = 60    # Time before retrying a failed remote webapp
#REMOTE_FIND_CACHE_DURATION = 300 # Time to cache remote metric find results

## Remote rendering settings
# Set to True to enable rendering of Graphs on a remote webapp
#REMOTE_RENDERING = True
# List of IP (and optionally port) of the webapp on each remote server that
# will be used for rendering. Note that each rendering host should have local
# access to metric data or should have CLUSTER_SERVERS configured
#RENDERING_HOSTS = []
#REMOTE_RENDER_CONNECT_TIMEOUT = 1.0

# If you are running multiple carbon-caches on this machine (typically behind a relay using
# consistent hashing), you'll need to list the ip address, cache query port, and instance name of each carbon-cache
# instance on the local machine (NOT every carbon-cache in the entire cluster). The default cache query port is 7002
# and a common scheme is to use 7102 for instance b, 7202 for instance c, etc.
#
# You *should* use 127.0.0.1 here in most cases
#CARBONLINK_HOSTS = ["127.0.0.1:7002:a", "127.0.0.1:7102:b", "127.0.0.1:7202:c"]
#CARBONLINK_TIMEOUT = 1.0

#####################################
# Additional Django Settings #
#####################################
# Uncomment the following line for direct access to Django settings such as
# MIDDLEWARE_CLASSES or APPS
#from graphite.app_settings import *

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'console': {
            'level':'ERROR',
            'class':'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
