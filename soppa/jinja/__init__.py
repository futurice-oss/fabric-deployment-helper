import jinja2

from soppa.contrib import *

class Jinja(Soppa):

    def get_tpl(self, path):
        loader = jinja2.FileSystemLoader([
            '/',
            self.local_module_conf_path(),
            self.module_conf_path(),
            self.soppa.basedir,
            ])
        environ = jinja2.Environment(loader=loader, undefined=jinja2.StrictUndefined)
        return environ.get_template(path)

jinja_task, jinja = register(Jinja)
