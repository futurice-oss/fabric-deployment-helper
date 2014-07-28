from soppa.contrib import *

import hashlib
import os, tempfile, re, inspect, sys, time, copy

class Pip(Soppa):
    requirements='{local_project_root}requirements.txt'
    packages_from='{local_project_root}dist/'
    packages_to='{www_root}dist/'
    extra_index=''
    # internal
    dirhashes = {}
    packages = {
        'apt': ['python-dev', 'python-setuptools'],
    }
    needs=[
        'soppa.virtualenv',
        'soppa.file',
        'soppa.operating',
        'soppa.linux',
        'soppa.rsync',
        'soppa.template',
    ]

    def filenameToRequirement(self, filename):
        """Converts 'package-name-1.2.3.tar.gz' to 'package-name==1.2.3'"""
        match = re.match(r'(.+)-(\d.+?)(\.tar\.gz|\.tar\.bz2|\.zip)$', filename)
        if not match:
            return None
        package, version, _extension = match.groups()
        return '{package}=={version}'.format(package=package, version=version)

    def requirementAsPackage(self, line):
        if '#egg=' in line:
            line = re.findall('#egg=(.*)', line)[0]
        return line

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

    # DIST
    def get_existing_files(self, folder=None):
        folder = self.fmt(folder or self.packages_from)
        return set(
            self.filenameToRequirement(filename)
            for filename in os.listdir(folder) if filename)

    def setup_missing_requirements(self, path=None, packages=[]):
        existing_files = self.get_existing_files()
        missing_requirements = tempfile.NamedTemporaryFile()
        if path:
            for raw_line in open(path):
                line = raw_line.strip()
                if not line or line.startswith('#') or requirementAsPackage(line) not in existing_files:
                    missing_requirements.write(raw_line)
        elif packages:
            for k in packages:
                missing_requirements.write(k+"\n")
        else:
            raise Exception()
        missing_requirements.flush()
        return missing_requirements

    def install_package(self, pipp=None):
        self.local(self.fmt('pip install'
              ' --no-use-wheel'
              ' -d {packages_from}'
              ' --exists-action=i'
              ' {extra_index}'
              ' {pipp}', pipp=pipp))

    def prepare_python_packages(self, requirements=None):
        # Download python packages (dependencies) into a local folder """
        self.local('mkdir -p {0}'.format(self.packages_from))
        if isinstance(requirements, list):
            pass
        else:
            use_req_file = self.fmt(requirements or self.requirements)
            requirements = self.requirements_as_pkgs(use_req_file)
        self.prepare_python_packages_from_list(requirements=requirements)

    def prepare_python_packages_from_list(self, requirements=[]):
        existing = self.get_existing_files()
        for k in requirements:
            if k not in existing:
                self.install_package(k)

        for k in requirements:
            self.add(k)

    def prepare_python_packages_from_file(self, requirements=None):
        use_req_file = self.fmt(requirements or self.requirements)
        self.prepare_python_packages_from_list(
                self.requirements_as_pkgs(use_req_file))

    # PIPPACKAGE
    def get_namespace(self):
        return hasattr(self, 'project') or '_default_'

    def add(self, name):
        self.packages.setdefault(self.get_namespace(), set())
        if self.package_exists(name):
            # on dupes, latest wins (TODO: use highest version)
            pkg_name = name.split('==')[0].lower()
            self.packages[self.get_namespace()] = set([
                k for k in self.packages[self.get_namespace()] if pkg_name not in k.lower()])
        else:
            self.packages[self.get_namespace()].add(name)

    def package_exists(self, name):
        pkg_name = name.split('==')[0]
        is_dupe = []
        if name.startswith('#'):
            is_dupe.append(True)
        for k in self.packages[self.get_namespace()]:
            if re.findall(pkg_name, k):
                is_dupe.append(True)
        return any(is_dupe)

    def all(self):
        if self.packages.has_key(self.get_namespace()):
            return self.packages[self.get_namespace()]
        return set()


    def install_python_packages(self):
        """ Installs Python packages
        - side-effect: .distlib/ being created to HOME """
        filename = '/tmp/packages_{0}.txt'.format(hashlib.sha256(str(time.time())).hexdigest())
        pkgs = "\n".join(self.all())
        f = self.file.tmpfile(pkgs)
        self.up(f.name, filename)
        with self.virtualenv.activate():
            self.run(self.fmt('HOME={packages_to} pip install'
                ' -f file://{packages_to}'
                ' -r {filename}'
                ' --no-index', filename=filename))
        f.close()

    def path_in_sync(self, path):
        h = self.file.directory_hash(path)
        curhash = copy.deepcopy(self.dirhashes.get(path, ''))
        self.dirhashes[path] = h
        return curhash==h

    def synchronize_python_packages(self, path=None, target_path=None):
        """ Sync downloaded local python packages folder """
        path = self.fmt(path or self.packages_from)
        target_path = self.fmt(target_path or self.packages_to)
        if not self.path_in_sync(path):
            #' --delete',
            self.rsync.rsync_up('-vP',
                     source=path,
                     target=target_path)

    def setup(self):
        if self.operating.is_linux():
            if not self.linux.binary_exists('pip'):
                self.sudo('easy_install pip')


    def install_package_global(self, name):
        self.sudo(self.fmt('pip install {name}'
            ' -f file://{packages_to}'
            ' --no-index --upgrade', name=name))

    def system_package_path(self, name):
        return os.path.normpath(self.sudo("python -c 'import {0}; import os; print os.path.dirname({1}.__file__)'".format(name, name)).strip()) + os.sep

    def sync_packages(self):
        self.prepare_python_packages()
        self.synchronize_python_packages()

    def update_packages(self, packages=[]):
        self.prepare_python_packages()
        if packages:
            self.prepare_python_packages(packages)
        self.synchronize_python_packages()
        self.virtualenv.setup()
        self.install_python_packages()

pip_task, pip = register(Pip)
