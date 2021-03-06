import hashlib
from soppa.contrib import *

class Package(Soppa):

    def setup(self):
        self.sudo('mkdir -p {packages_path}')

    def file_as_release(self, url, dest):
        """ Download a TAR file to be used as a release """
        download = '{}{}'.format(self.root.packages_path, self.id(url))
        if not self.exists(download):
            self.wget(url, download)
        self.sudo('mkdir -p {dest}', dest=dest)
        if self.package_in_dir(download, self.package_name(url)):
            self.sudo("tar --strip-components=1 -zxf {} -C {}".format(download, dest))
        else:
            self.sudo("tar -zxf {} -C {}".format(download, dest))

    def id(self, url):
        return hashlib.md5(url).hexdigest()

    def unpack(self, path):
        pass

    def wget(self, url, to):
        self.sudo("""wget --no-cookies \
        --no-check-certificate \
        "{0}" -L -O {1}""".format(url, to))

    def package_in_dir(self, pkg, needle):
        """ Determines if package contents are unpacked into a subfolder of identical name """
        with self.hide('output'):
            output = self.sudo("tar -tvf "+pkg+"|awk '{print $6}'")
        lines = [k for k in [line.strip() for line in unicode(output).split("\n")] if k]
        return all([k.startswith(needle) for k in lines])

    def package_name(self, url, by='/'):
        """ Guess package filename from URL """
        pkg = url.split(by)[-1]
        pkg = pkg.split('.')[0]
        return pkg
