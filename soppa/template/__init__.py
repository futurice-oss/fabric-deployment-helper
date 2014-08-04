import copy, tempfile

from soppa.contrib import *

from jinja2 import Template as JinjaTemplate

class Template(Soppa):
    needs = ['soppa.file']
    def determine_target_filename(self, a, b):
        af = a.split('/')[-1]
        filename = b + af
        if not b.endswith('/'):
            filename = b
        return filename

    def up(self, tpl, to, context={}, use_sudo=True):
        """ Render a template and upload to server
        - Jinja uses {{foo}} for formatting, Python uses {foo}
        """
        filename = self.determine_target_filename(
                formatloc(tpl, context),
                formatloc(to, context))
        assert '{' not in filename
        for k,v in context.iteritems():
            context[k] = formatloc(v, context)
        use_sudo = use_sudo or context.get('use_sudo', False)
        with open(tpl, 'r') as f:
            data = JinjaTemplate(f.read()).render(**context)
            with tempfile.NamedTemporaryFile() as tf:
                tf.write(data)
                tf.flush()
                diff_filename = copy.deepcopy(filename)
                # compare against root folder (that has the current version) instead of release folder
                if self.release_path in diff_filename:
                    diff_filename = diff_filename.replace(self.release_path, self.project_root)
                delta = self.file.diff_remote_to_local(diff_filename, tf.name)
                self.put(tf.name, filename, use_sudo=use_sudo)
        dlog.add(bucket='files', need=self.parent(), data={'source': tpl, 'target': filename, 'diff': delta})

template_task, template = register(Template)
