import os

from soppa.contrib import *
from soppa.deploy import DeployFrame

class SampleA(DeployFrame):
    needs=['soppa.sampleb']

    def hook_pre(self):
        print "conf.projectA:",self.env.project

    def pre(self):
        print "setup.projectA:", self.env.project

samplea_task, samplea = register(SampleA)
