from soppa.contrib import *

class ModB(Soppa):
    version='0.2'
    var = 'modb'
    def setup(self):
        return 2
