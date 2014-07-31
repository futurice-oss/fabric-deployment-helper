from soppa.contrib import *
from soppa.deploy import DeployFrame

class SampleB(DeployFrame):
    needs = ['soppa.template',]

    def go(self):
        print "setup.projectB:",self.project
        self.up('config/config.js', '/tmp/{project}.js')

sampleb_task, sampleb = register(SampleB)
