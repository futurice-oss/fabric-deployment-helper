from soppa.contrib import *

class Xs(Soppa):
    needs = ['soppa.template',]
    def testing(self):
        self.up('/tmp/bart', '/tmp/hi.there')

    def proceed(self, *args, **kwargs):
        """ XS.run """
        return super(Xs, self).setup(*args, **kwargs)


xs_task, xs = register(Xs)
