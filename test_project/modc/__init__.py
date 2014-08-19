from soppa.contrib import *

class ModParent(Soppa):
    voodoo = True

class ModC(ModParent):
    modc_left = 'left'
    var = 'modc'
    def voodoo(self):
        return False
modc = ModC
