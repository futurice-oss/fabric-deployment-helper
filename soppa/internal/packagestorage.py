
class PackageStorage(object):
    def __init__(self):
        self.already_added = []
        self.register = []

    def exists(self, name):
        return (name in self.register)

    def add(self, name):
        if not name:
            return
        if self.exists(self.requirementFormat(name)):
            self.already_added.append(name)
            return
        self.register.append(self.requirementFormat(name))

    def requirementFormat(self, name):
        return name

    def rem(self, name):
        try:
            idx = self.all_names(lower=True).index(name.lower())
            self.register.pop(idx)
        except ValueError:
            pass

    def all_names(self, lower=True):
        def fun(val):
            if lower:
                val = val.lower()
            return val
        return [fun(k[0]) for k in self.all()]

    def all(self):
        return self.register
