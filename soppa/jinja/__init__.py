import jinja2

from soppa.contrib import *

class Jinja(Soppa):
    jinja_undefined = 'StrictUndefined'

    def get_tpl(self, path):
        loader = jinja2.FileSystemLoader([
            '/',
            self.local_module_conf_path(),
            self.module_conf_path(),
            self.soppa.basedir,
            ])
        environ = jinja2.Environment(loader=loader, undefined=getattr(jinja2, self.jinja_undefined))
        return environ.get_template(path)
