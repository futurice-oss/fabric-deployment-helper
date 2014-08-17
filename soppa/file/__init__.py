import os, sys, time, copy, re, logging
import inspect, tempfile
from dirtools import Dir
import difflib

from soppa.contrib import *

log = logging.getLogger('soppa')

class File(Soppa):
    def directory_hash(self, path):
        return Dir(path).hash()

    def set_setting(self, filepath, text, ftype=None, backup=False, su=True):
        """ add setting 'text' to 'filepath', if not there """
        filepath = self.fmt(filepath)
        text = self.fmt(text)
        backup_file = filepath + '.bak'
        tmp_file = filepath + '.tmp'
        call = self.sudo if su else self.run
        call("cp {0} {1}".format(filepath, backup_file))
        call("cp {0} {1}".format(filepath, tmp_file))
        call('chown {0} {1}'.format(self.parent.deploy_user, tmp_file))

        with tempfile.NamedTemporaryFile(delete=True) as f:
            a = self.get_file(tmp_file, f)
            f.file.seek(0)
            if not self.contains_text(f.read(), text):
                f.write(text + "\n")
            f.file.seek(0)
            self.put(f.name, tmp_file)

        call("cp {0} {1}".format(tmp_file, filepath))
        call('rm {0}'.format(tmp_file))
        if not backup:
            call('rm {0}'.format(backup_file))

    def diff_remote_to_local(self, remote_file, local_file):
        with self.hide('output','warnings'), settings(warn_only=True):
            with tempfile.NamedTemporaryFile(delete=True) as f, open(local_file) as f2:
                a = self.get_file(remote_file, f)
                f.file.seek(0)
                diff = difflib.ndiff(f.readlines(), f2.readlines())
        return "".join(x for x in diff if x.startswith('- ') or x.startswith('+ ')).strip()

    def contains_text(self, haystack, needle):
        return (haystack.find(needle) <> -1)

    def tmpfile(self, data, suffix=''):
        tf = tempfile.NamedTemporaryFile(suffix=suffix)
        tf.write(data)
        tf.flush()
        return tf

file_task, file = register(File)
