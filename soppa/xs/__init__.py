from soppa.contrib import *

class Xs(Soppa):
    needs = ['soppa.template',]
    """ This is XS """
    def testing(self):
        print "XS!"
        #self.sudo('ls -laF')
        self.up('/tmp/bart', '/tmp/hi.there')

    def proceed(self, *args, **kwargs):
        """ XS.run """
        print "??"
        return super(Xs, self).setup(*args, **kwargs)


xs_task, xs = register(Xs)
