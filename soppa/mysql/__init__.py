from soppa.contrib import *

class Mysql(Soppa):
    user = 'root'
    name = ''
    password = ''
    needs = Soppa.needs+['soppa.pip','soppa.apt']

    def setup(self):
        with settings(warn_only=True):
            result = self.sudo('mysql -u{user} -p{password} -e "SELECT 1;"')
        with settings(warn_only=True):
            result2 = self.sudo('mysql -u{user} -p{password} -e "use {name};"')
            
        if result.failed or result2.failed:
            with settings(warn_only=True):
                self.create_database()

    def create_database(self):
        if not all([self.password, self.user, self.name]):
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
        mysql_cmd = self.fmt(scmd)
        shcmd = """mysql -u{user} -p{password} -e "{cmd}" {database} """.format(
                user=self.user,
                password=self.password,
                cmd=mysql_cmd,
                database=db)
        return self.sudo(shcmd)

mysql_task, mysql = register(Mysql)
