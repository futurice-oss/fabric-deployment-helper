from soppa.contrib import *

class SampleB(Soppa):
    needs = ['soppa.template',]

    def go(self):
        self.up('config/config.js', '/tmp/{project}.js')

sampleb_task, sampleb = register(SampleB)
