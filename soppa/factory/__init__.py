from soppa.contrib import *

class Factory(Soppa):
    """ Configurable modules """

    def get_module(self, choice):
        if '.' not in choice:
            choice = 'soppa.'+choice
        fun = import_string(choice)
        return fun

    def database(self, choice, action='setup'):
        mod = self.get_module(choice)
        fun = getattr(mod, choice)()
        getattr(fun, action)()

    def webserver(self, choice, action='setup'):
        mod = self.get_module(choice)
        fun = getattr(mod, choice)()
        getattr(fun, action)()

factory_task, factory = register(Factory)
