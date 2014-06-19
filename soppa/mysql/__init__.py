from soppa.contrib import *

class Mysql(Soppa):
    mysql_dbname='{project}'
    mysql_dbuser='root'
    mysql_dbpass=''
    packages={
        'apt': [
            'mysql-server',
            'libmysqlclient-dev'],
    }

    def setup(self):
        self.conf()

    def conf(self):
        with settings(warn_only=True):
            result = self.sudo('mysql -u{mysql_dbuser} -p{mysql_dbpass} -e "SELECT 1;"')
        with settings(warn_only=True):
            result2 = self.sudo('mysql -u{mysql_dbuser} -p{mysql_dbpass} -e "use {mysql_dbname};"')
            
        if result.failed or result2.failed:
            with settings(warn_only=True):
                self.rights()

    def rights(self):
        if not self.env.mysql_dbpass or not self.env.mysql_dbuser:
            raise Exception('Provide DATABASES settings')
        c = []
        c.append("create database if not exists {mysql_dbname}")
        c.append("DELETE FROM mysql.user WHERE User=''")
        c.append("flush privileges")
        c.append("GRANT ALL ON {mysql_dbname}.* TO {mysql_dbuser}@'%' IDENTIFIED BY '{mysql_dbpass}'")
        c.append("GRANT ALL ON {mysql_dbname}.* TO {mysql_dbuser}@'localhost' IDENTIFIED BY '{mysql_dbpass}'")
        c.append("GRANT FILE ON *.* TO {mysql_dbuser}@'%' IDENTIFIED BY '{mysql_dbpass}'")
        c.append("flush privileges")
        self.mysqlcmd(c)

    def mysqlcmd(self, cmd, db=''):
        scmd = '; '.join(cmd) + ';'
        mysql_cmd = scmd.format(**self.env)
        shcmd = """mysql -uroot -p -e "{0}" {1} """.format(mysql_cmd, db)
        return self.sudo(shcmd)

mysql_task, mysql = register(Mysql)
