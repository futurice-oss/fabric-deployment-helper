import copy

from soppa.contrib import *

class Template(Soppa):
    needs = ['soppa.file',
            'soppa.jinja',]

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
                self.fmt(tpl, context),
                self.fmt(to, context))
        assert '{' not in filename
        for k,v in context.iteritems():
            context[k] = self.fmt(v, context)
        data = self.jinja.get_tpl(tpl).render(**context)
        tf = self.file.tmpfile(data)
        # DIFF: compare against root folder (that has the current version) instead of release folder
        diff_filename = copy.deepcopy(filename)
        if self.release_path in diff_filename:
            diff_filename = diff_filename.replace(self.release_path, self.project_root)
        delta = self.file.diff_remote_to_local(diff_filename, tf.name)
        self.put(tf.name, filename, use_sudo=use_sudo)
        tf.close()
        dlog.add(bucket='files', need=self.parent(), data={'source': tpl, 'target': filename, 'diff': delta})

template_task, template = register(Template)
