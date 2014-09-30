import os

from soppa.contrib import *
from soppa.internal.packagestorage import PackageStorage

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
        target_path = os.path.join(path or self.defaults_conf_path(), self.path)
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

class PipHandler(PackageHandler):
    def setup_manager(self):
        if not self.get_installer().linux.binary_exists('pip'):
            self.get_installer().install_pip()

class Pip(PipHandler):
    path = 'requirements_global.txt'

    def get_installer(self):
        return getattr(self.need, 'pip')

    def install(self, packages):
        self.setup_manager()
        self.get_installer().install_packages_global(packages)

class PipVenv(Pip):
    path = 'requirements_venv.txt'

    def get_installer(self):
        return getattr(self.need, 'pip')

    def install(self, packages):
        self.setup_manager()
        self.get_installer().install_packages_venv(packages)
