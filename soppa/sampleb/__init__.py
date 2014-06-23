from soppa.contrib import *
from soppa.deploy import DeployFrame

class SampleB(DeployFrame):
    needs = ['soppa.template',]

    def hook_pre(self):
        print "conf.projectB:",self.project

    def pre(self):
        print "setup.projectB:",self.project
        self.up('config/config.js', '/tmp/{project}.js')

sampleb_task, sampleb = register(SampleB)
