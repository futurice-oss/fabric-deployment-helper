import os

from soppa.contrib import *

class PackageStorage(object):
    def __init__(self):
        self.already_added = []
        self.register = []

    def exists(self, name):
        return (name in self.register)

    def add(self, name):
        if not name:
            return
        if self.exists(self.requirementFormat(name)):
            self.already_added.append(name)
            return
        self.register.append(self.requirementFormat(name))

    def requirementFormat(self, name):
        return name

    def rem(self, name):
        try:
            idx = self.all_names(lower=True).index(name.lower())
            self.register.pop(idx)
        except ValueError:
            pass

    def all_names(self, lower=True):
        def fun(val):
            if lower:
                val = val.lower()
            return val
        return [fun(k[0]) for k in self.all()]

    def all(self):
        return self.register

class PackageHandler(object):
    """ list of lists [ [name, version] ] of packages """
    def __init__(self, need):
        self.package = PackageStorage()
        self.meta = PackageStorage()
        self.need = need
        self._CACHE = {}

    def defaults_conf_path(self):
        return os.path.join(self.need.module_path(),
                self.need.soppa.local_conf_path,
                'defaults',
                '')
    
    def target_conf_path(self):
        return os.path.join(self.need.soppa.local_path,
            self.need.soppa.local_conf_path,
            self.need.get_name(), '')

    def target_need_conf_path(self, path=None):
        return os.path.join(self.need.soppa.local_conf_path,
                    self.need.get_name(),
                    path or self.path)

    def read(self, path=None):
        target_path = os.path.join(self.defaults_conf_path(), path or self.path)
        if not os.path.exists(target_path):
            return
        for k in open(target_path).readlines():
            row = k.replace("\n","").strip()
            package = self.validate_package(row)
            self.package.add(package)
            meta = self.validate_meta(row)
            self.meta.add(meta)

    def write(self, path, packages):
        with open(path, "w+") as f:
            for namespace, data in packages.iteritems():
                if data:
                    f.write("\n".join(data) + "\n")

    def validate_package(self, package):
        if package and (not package[0].isalpha()):
            package = None
        return package

    def validate_meta(self, package):
        if self.validate_package(package):
            package = None
        return package

    def requirementName(self, name):
        return name.split('==')[0]

    def install(self):
        raise Exception("Unconfigured")

    def get_installer(self):
        raise Exception("Not configured")

class Apt(PackageHandler):
    path = 'apt_global.txt'

    def get_installer(self):
        return getattr(self.need, 'apt')

    def install(self, packages):
        self.get_installer().install(packages)

class Pip(PackageHandler):
    path = 'requirements_global.txt'

    def get_installer(self):
        return getattr(self.need, 'pip')

    def install(self, packages):
        self.get_installer().install_packages_global(packages)

class PipVenv(Pip):
    path = 'requirements_venv.txt'

    def get_installer(self):
        return getattr(self.need, 'pip')

    def install(self, packages):
        self.get_installer().install_packages_venv(packages)
