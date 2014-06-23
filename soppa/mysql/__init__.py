from soppa.contrib import *

class Mysql(Soppa):
    name='{project}'
    user='root'
    password=''
    packages={
        'apt': [
            'mysql-server',
            'libmysqlclient-dev'],
    }

    def setup(self):
        self.conf()

    def conf(self):
        with settings(warn_only=True):
            result = self.sudo('mysql -u{user} -p{password} -e "SELECT 1;"')
        with settings(warn_only=True):
            result2 = self.sudo('mysql -u{user} -p{password} -e "use {name};"')
            
        if result.failed or result2.failed:
            with settings(warn_only=True):
                self.rights()

    def rights(self):
        if not self.password or not self.user:
            raise Exception('Provide DATABASES settings')
        c = []
        c.append("create database if not exists {name}")
        c.append("DELETE FROM mysql.user WHERE User=''")
        c.append("flush privileges")
        c.append("GRANT ALL ON {name}.* TO {user}@'%' IDENTIFIED BY '{password}'")
        c.append("GRANT ALL ON {name}.* TO {user}@'localhost' IDENTIFIED BY '{password}'")
        c.append("GRANT FILE ON *.* TO {user}@'%' IDENTIFIED BY '{password}'")
        c.append("flush privileges")
        self.mysqlcmd(c)

    def mysqlcmd(self, cmd, db=''):
        scmd = '; '.join(cmd) + ';'
        mysql_cmd = scmd.format(**self.get_ctx())
        shcmd = """mysql -uroot -p -e "{0}" {1} """.format(mysql_cmd, db)
        return self.sudo(shcmd)

mysql_task, mysql = register(Mysql)
