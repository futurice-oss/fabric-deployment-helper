import hashlib, os, tempfile, re, inspect, sys, time, copy

from soppa.contrib import *

class Pip(Soppa):
    packages_from = '{soppa.local_path}dist/'
    packages_to = '{www_root}dist/'
    extra_index = ''
    _dirhashes = {}

    def setup(self):
        self.sudo('mkdir -p {packages_path}')
        self.sudo('mkdir -p {packages_to}')

        if not self.linux.binary_exists('pip'):
            self.install_pip()

    # DIST
    def filenameToRequirement(self, filename):
        """ Converts 'package-name-1.2.3.tar.gz' to 'package-name==1.2.3'"""
        match = re.match(r'(.+)-(\d.+?)(\.tar\.gz|\.tar\.bz2|\.zip)$', filename)
        if not match:
            return None
        package, version, _extension = match.groups()
        return '{package}=={version}'.format(package=package, version=version)

    def get_existing_files(self, folder=None):
        folder = self.fmt(folder or self.packages_from)
        return set(
            self.filenameToRequirement(filename)
            for filename in os.listdir(folder) if filename)

    def requirementAsPackage(self, line):
        if '#egg=' in line:
            line = re.findall('#egg=(.*)', line)[0]
        return line

    def flush_packages_to_file(self, packages):
        # TODO: need to add --index-url
        missing_requirements = tempfile.NamedTemporaryFile()
        for package in packages:
            missing_requirements.write("\n"+package)
        missing_requirements.flush()
        return missing_requirements

    def compare_requirements(self, path):
        """ Compare local dist/ contents to installable packages """
        existing_files = self.get_existing_files()
        missing_requirements = []
        for raw_line in open(path):
            line = raw_line.strip()
            pkg = self.requirementAsPackage(line)
            if any([line.startswith(char) for char in ['#','--']]):
                continue
            if pkg not in existing_files:
                missing_requirements.append(pkg)
        return missing_requirements

    def download(self, requirements, packages_path=None, new_only=False):
        packages_path = self.fmt(packages_path or self.packages_from)
        if new_only:
            missing = self.compare_requirements(path=requirements)
            tmp_file = self.flush_packages_to_file(missing)
            requirements = tmp_file.name
        self.local(self.fmt('pip install'
              ' --no-use-wheel'
              ' -d {packages_path}'
              ' --exists-action=i'
              ' -r {requirements}', requirements=requirements,
              packages_path=packages_path))

    def install_packages_from_file(self, filename, envflags=[], flags=[], use_sudo=False):
        fn = self.sudo if use_sudo else self.run
        fn(self.fmt('{envflags} pip install'
            ' -f file://{packages_to}'
            ' -r {filename}'
            ' --no-index {flags}',
                filename=filename,
                envflags=" ".join(envflags),
                flags=" ".join(flags)))
    
    def upload_packages_to_install_as_file(self, packages):
        filename = '/tmp/packages_{0}.txt'.format(hashlib.sha256(str(time.time())).hexdigest())
        pkgs = "\n".join(packages)
        f = self.file.tmpfile(pkgs)
        self.up(f.name, filename)
        f.close()
        return filename

    def install_packages_global(self, packages=[]):
        filename = self.upload_packages_to_install_as_file(packages)
        self.install_packages_from_file(filename, flags=['--upgrade'], use_sudo=True)

    def install_packages_venv(self, packages=[]):
        """ Installs Python packages
        - side-effect: .distlib/ being created to HOME """
        filename = self.upload_packages_to_install_as_file(packages)
        with self.virtualenv.activate():
            self.install_packages_from_file(filename, envflags=['HOME={packages_to}'])

    def path_in_sync(self, path):
        # TODO: save directory-hash for future, instead of being run-specific
        h = self.file.directory_hash(path)
        curhash = copy.deepcopy(self._dirhashes.get(path, ''))
        self._dirhashes[path] = h
        return curhash==h

    def sync(self, path=None, target_path=None):
        """ Copy local copies of packages to a remote location """
        path = self.fmt(path or self.packages_from)
        target_path = self.fmt(target_path or self.packages_to)
        if not self.path_in_sync(path):
            #' --delete'; removed, as target directory is shared between all projects
            self.rsync.rsync_up('-vP',
                     source=path,
                     target=target_path)

    def install_pip(self):
        """ NOTE: pip can remain in broken state, requires removing old /usr/local/bin/pip* files first """
        path = '{path}dist/'
        self.sudo('mkdir -p {0}'.format(path))
        with self.cd(path):
            self.sudo('rm -f get-pip.py')
            self.sudo('wget -S https://bootstrap.pypa.io/get-pip.py --no-check-certificate')
            self.sudo('python get-pip.py --force --no-use-wheel')

    def system_package_path(self, name):
        rs = self.sudo("python -c 'import {0}; import os; print os.path.dirname({1}.__file__)'".format(name, name))
        return os.path.normpath(unicode(rs).strip()) + os.sep
