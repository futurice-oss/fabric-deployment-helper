from soppa.contrib import *

class SampleB(Soppa):
    needs = ['soppa.template',]

    def setup(self):
        self.up('config/config.js', '/tmp/{project}.js')

sampleb_task, sampleb = register(SampleB)
