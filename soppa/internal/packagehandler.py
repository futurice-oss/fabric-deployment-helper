import os

class PackageHandler(object):
    """ list of lists [ [name, version] ] of packages """
    def __init__(self, path, need):
        self.path = path
        self.register = []
        self.already_added = []
        self.need = need

    def exists(self, name):
        pass

    def add(self, name):
        if self.exists(name):
            self.already_added.append(name)
            return
        self.register.append([self.requirementFormat(name)])

    def requirementFormat(self, name):
        return name

    def rem(self, name):
        try:
            idx = self.all_names(lower=True).index(name.lower())
            self.register.pop(idx)
        except ValueError:
            pass

    def all(self):
        return self.register

    def all_names(self, lower=True):
        def fun(val):
            if lower:
                val = val.lower()
            return val
        return [fun(k[0]) for k in self.all()]

    def defaults_conf_path(self):
        return os.path.join(self.need.module_path(),
                self.need.local_conf_path,
                '')
    
    def target_conf_path(self):
        return os.path.join(self.need.local_project_root,
            self.need.local_conf_path,
            self.need.get_name(), '')

    def read(self):
        target_path = os.path.join(self.defaults_conf_path(), self.path)
        rs = []
        if not os.path.exists(target_path):
            return rs
        for k in open(target_path).readlines():
            package = k.replace("\n","")
            if not package:
                continue
            rs.append(package)
        return rs

class AptPackage(PackageHandler):
    pass

class PipPackage(PackageHandler):
    def filenameToRequirement(self, filename):
        """Converts 'package-name-1.2.3.tar.gz' to 'package-name==1.2.3'"""
        match = re.match(r'(.+)-(\d.+?)(\.tar\.gz|\.tar\.bz2|\.zip)$', filename)
        if not match:
            return None
        package, version, _extension = match.groups()
        return '{package}=={version}'.format(package=package.lower(), version=version)

    def requirementAsPackage(self, line):
        # foo==x.y.z
        if '#egg=' in line:
            line = re.findall('#egg=(.*)', line)[0]
        return line.lower()

    def requirementName(self, name):
        return name.split('==')[0]

    def requirementVersion(self, name):
        try:
            return name.split('==')[1] or ''
        except IndexError:
            return ''

    def requirements_as_pkgs(self, requirements_file):
        if not os.path.isfile(requirements_file):
            return []
        all_requirements = set()
        for raw_line in open(requirements_file):
            line = raw_line.strip()
            if line.startswith('#'):
                continue
            if line:
                all_requirements.add(self.requirementAsPackage(line))
        return all_requirements

    def get_namespace(self):
        return hasattr(self, 'project') or '_default_'

    def valid_package(self, name):
        return (not name.startswith('#'))

    def remove_package(self, name):
        pass

    def package_exists(self, name):
        return self.requirementName(name).lower() in\
                [self.requirementName(k).lower() for k in self.packages[self.get_namespace()]]\
                is None

    def all_packages(self):
        if self.packages.has_key(self.get_namespace()):
            return self.packages[self.get_namespace()]
        return set()

