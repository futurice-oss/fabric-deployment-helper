from soppa.contrib import *

class SampleA(Soppa):
    needs=['soppa.sampleb']

    def setup(self):
        pass

samplea_task, samplea = register(SampleA)
