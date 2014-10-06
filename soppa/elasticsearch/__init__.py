import os

from soppa.contrib import *

class ElasticSearch(Soppa):
    url = 'https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.3.2.tar.gz'
    servername = 'elasticsearch.dev'

    def setup(self):
        self.java.setup()

        self.package.file_as_release(self.url, dest=self.path)

        self.action('up', 'elasticsearch_nginx.conf', '{nginx_conf_dir}',
                handler=['nginx.restart'],
                when=lambda x: x.soppa_web_server=='nginx')

        self.action('up', 'elasticsearch_supervisor.conf', '{supervisor_conf_dir}',
                handler=['supervisor.restart'],
                when=lambda x: x.soppa_proc_daemon=='supervisor')

    def health(self):
        # http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/_cluster_health.html
        f=1
        #/_cat/health?v
