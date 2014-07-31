from soppa.contrib import *

from soppa.deploy import DeployFrame

class Package(DeployFrame):
    def file_as_release(self, url):
        """ Download a file to be used as a release """
        package_pkg = self.package_path(url)
        self.dirs()
        if not self.exists(package_pkg):
            with self.cd('{basepath}'):
                self.wget(url, package_pkg)
        with self.cd('{basepath}'):
            self.run('mkdir -p releases/{release}')
            if self.package_in_dir(package_pkg, self.package_name(url)):
                self.sudo("tar --strip-components=1 -zxf {0} -C releases/{1}"\
                    .format(package_pkg, self.release))
            else:
                self.sudo("tar -zxf {0} -C releases/{1}"\
                    .format(package_pkg, '{release}'))
        self.ownership()
        self.symlink_release()

    def dummy(self, name=None):# for testing
        return name

    def wget(self, url, to):
        self.sudo("""wget --no-cookies \
        --no-check-certificate \
        "{0}" -L -O {1}""".format(url, to))

    def package_in_dir(self, pkg, needle):
        output = self.sudo("tar -tvf "+pkg+"|awk '{print $6}'")
        lines = [k for k in [line.strip() for line in output.split("\n")] if k]
        return all([k.startswith(needle) for k in lines])

    def package_path(self, url):
        pkg = url.split('/')[-1]
        to = '{basepath}packages/'
        return to + pkg

    def package_name(self, url, by='/'):
        pkg = url.split(by)[-1]
        pkg = pkg.split('.')[0]
        return pkg

    def download_package(self):
        with self.cd('{basepath}'):
            self.run('mkdir -p releases/{release}')
            self.run('tar zxf packages/{release}.tar.gz -C releases/{release}')
        self.local('rm {deploy_tarball}')

package_task, package = register(Package)
