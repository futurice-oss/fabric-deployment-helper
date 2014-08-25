from soppa.contrib import *

class ModA(Soppa):
    version='0.1'
    needs=['test_project.modb']
    var = 'moda'
    def setup(self):
        return 1
