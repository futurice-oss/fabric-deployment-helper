import os, sys, time, copy, re, logging
import inspect, tempfile
from dirtools import Dir

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
        call('chown {0} {1}'.format(self.deploy_user, tmp_file))

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

    def append_string_to_file(self, filepath, text):
        with open(filepath, "a+") as f:
            f.write(text + "\n")

    def contains_text(self, haystack, needle):
        return (haystack.find(needle) <> -1)

    def match_str_in_file(self, fname, text):
        pat = re.compile(r"%s"%re.escape(text), re.MULTILINE)
        with open(fname) as f:
            res = f.read()
        return (res.find(text) <> -1)

    def tmpfile(self, data, suffix=''):
        tf = tempfile.NamedTemporaryFile(suffix=suffix)
        tf.write(data)
        tf.flush()
        return tf

file_task, file = register(File)
