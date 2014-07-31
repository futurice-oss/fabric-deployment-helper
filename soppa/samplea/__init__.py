import os

from soppa.contrib import *
from soppa.deploy import DeployFrame

class SampleA(DeployFrame):
    needs=['soppa.sampleb']

    def go(self):
        print "setup.projectA:", self.project

samplea_task, samplea = register(SampleA)
