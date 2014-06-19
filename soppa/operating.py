from soppa.contrib import *

import sys

class Operating(Soppa):
    def is_linux(self):
        """ Check host operating system when used in combination with aslocal(); otherwise assume Linux """
        if not self.env.local_deployment:
            return True
        return self.is_a('linux')

    def is_osx(self):
        """ Check host operating system when used in combination with aslocal(); otherwise assume Linux
        - allows local installation for development
        """
        if not self.env.local_deployment:
            return False
        return self.is_a('darwin')

    def is_a(self, name):
        return any(k in sys.platform for k in [name])

operating_task, operating = register(Operating)
