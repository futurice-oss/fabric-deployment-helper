from soppa.contrib import *

class Java(Soppa):
    """
    Installs Oracle Java
    - latest versions at http://www.oracle.com/technetwork/java/javase/downloads/
    - tested on Debian Wheezy
    """
    url = 'http://download.oracle.com/otn-pub/java/jdk/7u55-b13/jdk-7u55-linux-x64.tar.gz'
    pkg = "/opt/java.tar.gz"
    path = "/opt/java-oracle/"

    def setup(self):
        self.sudo("mkdir -p {java_path}")
        if not self.exists(self.java_pkg):
            self.sudo("""wget --no-cookies \
            --no-check-certificate \
            --header "Cookie: oraclelicense=accept-securebackup-cookie" \
            "{java_url}" -O {java_pkg}""")
            self.sudo("tar -zxf {java_pkg} -C {java_path}")
        self.conf()
        self.java_version = self.get_java_version()

    def conf(self):
        self.java_home = self.get_java_home()
        self.sudo("update-alternatives --install /usr/bin/java java {java_home}/bin/java 20000")
        self.sudo("update-alternatives --install /usr/bin/javac javac {java_home}/bin/javac 20000")
        self.sudo("touch /etc/environment")
        self.file.set_setting('/etc/environment', 'JAVA_HOME={0}'.format(self.java_home))

    def get_java_version(self):
        return unicode(self.sudo("cd {java_path} && ls -t|head -1")).strip()

    def get_java_home(self):
        return "{0}{1}".format(self.java_path, self.get_java_version())

    def check(self):
        pass
        # update-alternatives --config java
        # java -version
