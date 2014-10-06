import ConfigParser
import copy
import collections
from soppa.internal.tools import generate_config
from soppa.internal.mixins import ReleaseMixin
from pprint import pprint as pp

def load(path):
    c = Config(path=path)
    return c.values()

class Config(object):
    """ Main configuration in INI format
    - Has custom list-formatting support
    """
    def __init__(self, path=None, parser=None, allow_no_value=True):
        self.path = path
        self.c = parser or ConfigParser.SafeConfigParser(allow_no_value=allow_no_value)

    def read(self):
        if not self.path:
            return
        self.c.read(self.path)

    def save(self):
        if not self.path:
            return
        with open(self.path, 'wb') as f:
            self.c.write(f)

    def values(self):
        self.read()
        c = {}

        for section in self.c.sections():
            c.setdefault(section, {})
            for k,v in self.c.items(section):
                c[section][k] = self.read_fmt_value(v)
        return c

    def read_fmt_value(self, v):
        # ConfigParser return strings by default, and does not support lists.
        def list_fmt(v):
            if v.startswith('[') and v.endswith(']'):
                v = copy.deepcopy(v)
                v = v[1:-1].split(',')
                v = [k.replace('\n','') for k in v if k]
                v = [k for k in v if k]
            return v
        def boolean_fmt(v):
            if v=='True':
                v = True
            elif v=='False':
                v = False
            return v
        def float_fmt(v):
            if not isinstance(v, basestring):
                return v
            try:
                return float(v)
            except ValueError:
                return v
        def int_fmt(v):
            if not isinstance(v, basestring):
                return v
            try:
                return int(v)
            except ValueError:
                return v

        def fmt(v):
            v = list_fmt(v)
            v = boolean_fmt(v)
            v = int_fmt(v)
            v = float_fmt(v)
            return v

        return fmt(v)

    def write_fmt_value(self, v):
        def list_fmt(v):
            if isinstance(v, list) or isinstance(v, tuple):
                v = ",\n".join(v)
                v = "[\n{}]".format(v)
            return v
        def fmt(v):
            v = list_fmt(v)
            return unicode(v)
        return fmt(v)

    def update(self, section, data, overwrite=False):
        """ section=None is [DEFAULT] """
        self.read()

        if not data:
            return

        data = collections.OrderedDict(sorted(data.items()))

        if section and not self.c.has_section(section):
            self.c.add_section(section)

        for k,v in data.iteritems():
            if not overwrite and not self.c.has_option(section, k):
                self.c.set(section, k, self.write_fmt_value(v))

        self.save()

import os
def update_config(cls, path=None, ctx={}):
    from soppa.jinja import Jinja
    # TODO: better way to temporarily patch values
    original_value = Jinja.jinja_undefined
    Jinja.jinja_undefined = 'Undefined'
    os.environ['DRYRUN'] = '1'

    c = Config(path=path)

    instance = cls(ctx)
    instance.setup()

    gl_default = generate_config(instance)
    gl = generate_config(instance, include_cls=[ReleaseMixin])
    gl_final = {}
    for k,v in gl.iteritems():
        if k not in gl_default:
            gl_final[k] = v
    c.update('globals', gl_final)

    instances = instance.log.get_action_instances()
    instances += instance.get_default_modules()
    instances_child = instances
    instances_configuration = instances

    # ensure main instance is included in configuration
    if not any([isinstance(k, type(instance)) for k in instances]):
        instances_configuration.append(instance)

    # ensure package managers are included
    if instances:
        packman = instances[0].packman()
        for handler in packman.unique_handlers():
            instances_configuration.insert(0, handler.get_installer())

    for instance in instances_configuration:
        data = generate_config(instance)
        c.update(instance.get_name(), data)

    Jinja.jinja_undefined = original_value
    os.environ.pop('DRYRUN', False)

    # remove duplicates
    r = []
    for instance in instances_child:
        if not any([isinstance(k, type(instance)) for k in r]):
            r.append(instance)

    return r, c.values()
