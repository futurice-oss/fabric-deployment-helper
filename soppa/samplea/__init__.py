from soppa.contrib import *

class SampleA(Soppa):
    needs=['soppa.sampleb']

    def go(self):
        pass

samplea_task, samplea = register(SampleA)
