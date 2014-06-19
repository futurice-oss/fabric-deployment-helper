from soppa.contrib import *

class ModA(Soppa):
    version='0.1'
    needs=['test_project.modb']
    packages={
        'pip':'config/requirements.txt',
        'apt': ['curl'],
        }
    def setup(self):
        return 1
moda = ModA
