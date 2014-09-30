import os
from soppa.internal.tools import import_string

class PackageManager(object):
    def __init__(self, instance):
        self.instance = instance
        self._CACHE = {}
        self.handlers = []
        self.storages = ['package','meta']

        self.set_handler(instance)

    def set_handler(self, instance):
        for name in instance.soppa.packmans:
            handin = import_string(name)(need=instance)
            self.handlers.append(handin)

    def unique_handlers(self):
        key = 'unique_handlers'
        if not self._CACHE.get(key):
            self._CACHE[key] = [import_string(name)(need=self.instance) for name in self.instance.soppa.packmans]
        return self._CACHE[key]
            
    def get_packages(self, path=None):
        """ Flatten packages into a single source of truth, ensuring needs do not override existing project dependencies.
        """
        rs = {k:{'meta':[], 'package':[]} for k in self.unique_handlers()}
        def handler_group(handler):
            for uh in self.unique_handlers():
                if handler.__class__.__name__ == uh.__class__.__name__:
                    return uh
            raise Exception('Unknown handler')

        for handler in self.handlers:
            handler.read(path=path)
            for storage in self.storages:
                for package in getattr(handler, storage).all():
                    existing_package_names = [handler.requirementName(k) for k in rs[handler_group(handler)][storage]]
                    if handler.requirementName(package) not in existing_package_names:
                        rs[handler_group(handler)][storage].append(package)
        return rs

    def write_packages(self, packages):
        """ One project, single requirement files (encompasses all dependencies).
        To install everything need multiple installs.
        Does not overwrite existing settings.
        """
        for handler, pkg in packages.iteritems():
            filepath = handler.target_need_conf_path()
            if not os.path.exists(os.path.dirname(filepath)):
                self.instance.local('mkdir -p {}'.format(os.path.dirname(filepath)))#TODO: elsewhere; Dir.ensure_exists(path)
            if not os.path.exists(filepath):
                handler.write(filepath, pkg)

    def sync_packages(self, packages):
        for handler, pkg in packages.iteritems():
            filepath = handler.target_need_conf_path()
            if pkg['package']:
                handler.get_installer().sync()

    def download_packages(self, packages):
        """ Download local copies of packages """
        for handler, pkg in packages.iteritems():
            filepath = handler.target_need_conf_path()
            if pkg['package']:
                handler.get_installer().download(filepath, new_only=True)

    def install_packages(self, packages):
        for handler, pkg in packages.iteritems():
            if pkg['package']:
                handler.install(pkg['package'])
