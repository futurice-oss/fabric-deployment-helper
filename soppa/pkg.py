
class Pkg(object):
    def handle(self, settings): 
        for name,items in settings.get('packages', {}).iteritems():
            getattr(self, 'handle_{0}'.format(name))(items)

    def handle_pip(self, packages):
        f=1

    def handle_apt(self, packages):
        f=1
