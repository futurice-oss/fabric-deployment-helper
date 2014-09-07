import ConfigParser
from soppa.internal.tools import generate_config

class Config(object):
    """ Main configuration in INI format """
    def __init__(self, path='config.ini', parser=None):
        self.path = path
        self.c = parser or ConfigParser.SafeConfigParser()

    def read(self):
        self.c.read(self.path)

    def save(self):
        with open(self.path, 'wb') as f:
            self.c.write(f)

    def values(self):
        self.read()
        c = {}
        for section in self.c.sections():
            c.setdefault(section, {})
            for k,v in self.c.items(section):
                c[section][k] = v
        return c

    def update(self, section, data, overwrite=False):
        """ section=None is [DEFAULT] """
        self.read()

        if not data:
            return

        if section and not self.c.has_section(section):
            self.c.add_section(section)

        for k,v in data.iteritems():
            if not overwrite and not self.c.has_option(section, k):
                self.c.set(section, k, unicode(v))

        self.save()

def update_config(cls, path='config.ini'):
    import os
    from soppa.jinja import Jinja
    # TODO: better way to temporarily patch values
    original_value = Jinja.jinja_undefined
    Jinja.jinja_undefined = 'Undefined'
    os.environ['DRYRUN'] = '1'

    c = Config(path=path)

    instance = cls()
    config = c.values().get(instance.get_name(), {})

    instance = cls(config)
    instance.setup()
    instances = instance.log.get_action_instances()
    # ensure main instance is included
    if not any([isinstance(k, type(instance)) for k in instances]):
        instances.append(instance)

    for instance in instances:
        data = generate_config(instance)
        c.update(instance.get_name(), data)

    Jinja.jinja_undefined = original_value
    os.environ.pop('DRYRUN', False)
