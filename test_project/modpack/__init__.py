from soppa.contrib import *

class ModPack(Soppa):
    needs = ['test_project.modc']
    soreal = True
    modc_soreal = False
    modc_mangle = '{modc.modc_left}'
    modc_mangle_self = '{self.modc.modc_left}'
    def dummy(self, name=None):
        return name
