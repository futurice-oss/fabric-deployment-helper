import unittest, copy, os
import shutil

from soppa.contrib import *
from soppa.internal.ingredients import Pip, Django, File, Template, Virtualenv, Graphite

from soppa.internal.tools import ObjectDict, Upload, generate_config
from soppa.internal.runner.default import Runner
from soppa.internal.config import update_config
from soppa.internal.mixins import DirectoryMixin

from ..moda import ModA
from ..modb import ModB
from ..modc import ModC
from ..modd import ModD
from ..mode import ModE
from ..modf import ModF
from ..modpack import ModPack

class BaseSuite(unittest.TestCase):
    pass

TARGET_TO_SPOIL="""
something here
"""

SAMPLE_SPOIL="""

#=target.operations.api.run
i am
in the code
#>

#=target.operations.api.sudo
hello world
#>
"""

SAMPLE_SPOIL_UPDATE="""
#=target.operations.api.sudo
hello sunny world
#>
"""

class TaskClass(object):
    def task_method(self):
        return 50
taskclass = TaskClass()

@task
def my(cmd=None):
    return 60

@task
def seq(a, b):
    return '{0}={1}'.format(a, b)

def three():
    return 3

class SoppaTest(BaseSuite):
    def setUp(self):
        self.base = copy.deepcopy(env)

    def tearDown(self):
        env = self.base

    def test_log_changes(self):
        m = ModPack()
        self.assertFalse(m.isDirty())
        m.log.add('files', m.get_name(), {'diff':'!','source':'foo','target':'bar'})
        self.assertTrue(m.isDirty())

    def test_packages_possibilities(self):
        m = ModPack()
        self.assertTrue(m.packman().unique_handlers())
        self.assertTrue(m.has_need('modc'))
        self.assertFalse(m.has_need('foo'))
        self.assertFalse(m.has_need('project'))

    def test_kwargs_do_not_overwrite_needs(self):
        p = Pip(ctx={'virtualenv':{}})
        self.assertFalse(p.has_need('virtualenv'))
        p.needs.append('virtualenv')
        self.assertTrue(p.has_need('virtualenv'))
        self.assertFalse(p.virtualenv != {})

        p = Pip(dict(virtualenv_local_conf_path='/tmp/'))
        self.assertEquals(p.virtualenv.local_conf_path, '/tmp/')
        v = Virtualenv()
        with self.assertRaises(AttributeError):
            v.local_conf_path

    def test_variable_namespacing(self):
        ctx = {'host': 'localhost.here'}
        i = Graphite(ctx=ctx)
        self.assertEquals(i.host, ctx['host'])

    def test_mlcd(self):
        base_dir = os.getcwd()
        there = here()
        s=Soppa()
        with s.mlcd(os.path.join('../..', 'soppa/supervisor/')):
            self.assertEquals(os.getcwd(), os.path.join(base_dir, 'soppa/supervisor'))
            self.assertEquals(os.getcwd(), os.path.normpath(os.path.join(there, '../../soppa/supervisor/')))

    def test_scoped_env(self):
        p = Pip()
        v = Virtualenv()
        self.assertTrue(p.packages_to)
        self.assertTrue(v.pip.packages_to)

    def test_formatting(self):
        m = ModPack()
        with self.assertRaises(KeyError):
            self.assertEquals(m.fmt('{foo}{bar}'), '{foo}{bar}')
        ctx = {'foo':'FOO'}
        with self.assertRaises(KeyError):
            self.assertEquals(m.fmt('{foo}{bar}', **ctx), 'FOO{bar}')
        self.assertEquals(m.fmt('{foo}{bar}', bar='BAR', **ctx), 'FOOBAR')

        ctx['foo'] = '{bar}'
        with self.assertRaises(KeyError):
            self.assertEquals(m.fmt('{foo}', **ctx), '{bar}')
        ctx = {'foo':'{bar}','bar':'BAR'}
        self.assertEquals(m.fmt('{foo}', **ctx), 'BAR')

        ctx['town'] = 'Helsinki'
        self.assertEquals(m.fmt('{town}', **ctx), 'Helsinki')

        self.assertEquals(m.fmt('{foo_bar}', **{'foo_bar': 'oh'}), 'oh')
        c = {'foo': ObjectDict({'bar': 'oh.oh'})}
        self.assertEquals(m.fmt('{foo.bar}', **c), 'oh.oh')

        u = Upload('config/statsd_supervisor.conf', '{packages_from}', instance=Pip(), caller_path='/tmp/')
        self.assertTrue(all('{' not in k for k in u.args))

        s = 'mkdir -p {basepath}{packages,releases,media,static,dist,logs,config/vassals/,pids,cdn}'
        self.assertTrue('/x/' in m.fmt(s, **dict(basepath='/x/')))

    def test_formatting_bash(self):
        m = ModPack()
        ctx = {'foo': 'FOO'}
        self.assertEquals(m.fmt('{foo} {"print $2"}', **ctx), 'FOO {"print $2"}')
        self.assertEquals(m.fmt('{foo}', **ctx), 'FOO')

    def test_formatting_invalid_string(self):
        m = ModPack()
        s = """'ifconfig -a eth1|grep "inet addr"|awk '{gsub("addr:","",$2); print $2}'"""
        self.assertEquals(m.fmt(s), s)

    def test_formatting_fun(self):
        m = ModPack()
        def lalafun(kw):
            rs = 100
            return rs
        ctx = {'lala': lalafun}
        r = m.fmt('{lala}', **ctx)
        self.assertFalse('<function' not in r)
        with self.assertRaises(AssertionError):
            self.assertEquals(r, '100')

    def test_set_setting(self):
        env.local_deployment = True
        start_str = """hello world\nhawai\n"""
        ff = File({})
        f = ff.tmpfile(start_str)
        f.seek(0)
        ff.set_setting(f.name, 'foobar', su=False)
        f.seek(0)
        self.assertEqual(f.read(), start_str + "foobar\n")

    def test_target_filename(self):
        template = Template({})
        self.assertEquals(template.determine_target_filename('/1/foo.txt', '/tmp/'), '/tmp/foo.txt')
        self.assertEquals(template.determine_target_filename('/1/foo.txt', '/tmp/bar.txt'), '/tmp/bar.txt')
        self.assertEquals(template.determine_target_filename('/1/foo.txt', '/tmp'), '/tmp')

    def test_config_gathering(self):
        m = ModPack()
        self.assertEquals(generate_config(m, include_cls=[ReleaseMixin])['project'], m.project)
        m = ModPack(project='custom-name')
        self.assertEquals(generate_config(m, include_cls=[ReleaseMixin])['project'], m.project)

        m = ModPack()
        self.assertNotEquals(m.project, m.modc.project)
        m = ModPack(dict(project='same'))
        self.assertEquals(m.project, m.modc.project)

def overwrite(f, data):
    f.seek(0)
    f.write(data)
    f.truncate()

class PatchTest(BaseSuite):
    def test_env_function(self):
        m = ModPack()
        def _(kw={}):
            return 100
        with self.assertRaises(AssertionError):
            self.assertEqual(m.fmt(_), 100)

class ModuleTest(BaseSuite):

    def test_package(self):
        self.assertEquals(ModPack({}).dummy('John'), 'John')

    def test_module_packages(self):
        ma = ModA(dict(project='name_moda', modb_project='name_modb_override'))
        mb = ModB(dict(project='name_modb'))
        ma.setup()
        self.assertNotEqual(ma.version, mb.version)
        self.assertEquals(ma.project, 'name_moda')
        self.assertEquals(mb.project, 'name_modb')
        self.assertEquals(ma.modb.project, 'name_modb_override')
        ma = ModA({'project': 'king'})
        self.assertEquals(ma.project, 'king')

    def test_module_contains_variables_from_dependent_modules(self):
        ma = ModA()
        self.assertEquals(ma.var, 'moda')
        self.assertEquals(ma.modb.var, 'modb')
        with self.assertRaises(AttributeError):
            ma.ModC.var

    def test_module_var_mutability(self):
        md = ModD()
        self.assertNotEquals(md.something, md.modf.something)
        md = ModD({'something': 3})
        self.assertEquals(md.something, md.modf.something)
        md = ModD({'modd_something': 3})
        self.assertNotEquals(md.something, md.modf.something)
        self.assertTrue(md.something == md.modd_something == 3)

    def test_module_variable_waterfall(self):
        """
        child_foo -> self.child.foo/child_foo
        self_child_foo -> self.child.foo/child_foo
        """
        md = ModD()
        self.assertEquals(md.modf.modf_shout, 'hello')
        self.assertEquals(md.modf.shout, 'hello')
        md = ModD(dict(modf_shout='hello'))
        self.assertEquals(md.modf.modf_shout, 'hello')
        self.assertEquals(md.modf.shout, 'hello')

        md = ModD(dict(modd_modf_shout='woof'))
        self.assertEquals(md.modf.modf_shout, 'woof')
        self.assertEquals(md.modf.shout, 'woof')
        md = ModD(dict(modf_shout='bark', modd_modf_shout='woof'))
        self.assertEquals(md.modf.modf_shout, 'woof')
        self.assertEquals(md.modf.shout, 'woof')
        md = ModD(dict(modd_modf_shout='woof', modf_shout='bark'))
        self.assertEquals(md.modf.modf_shout, 'woof')
        self.assertEquals(md.modf.shout, 'woof')

        md = ModD(dict(modd_modf_shout='hello'))
        self.assertEquals(md.modf.shout, 'hello')

        config = dict(
                modd_modf_shout='hello',
                mode_modf_shout='bye',
                some_global='global',)
        md = ModD(config)
        me = ModE(config)
        self.assertEquals(md.modf.shout, 'hello')
        self.assertEquals(me.modf.shout, 'bye')
        self.assertEquals(me.modf.some_global, 'global')

        mf = ModF(dict(modf_shout='omg'))
        self.assertEquals(mf.shout, 'omg')
        self.assertEquals(mf.modf_shout, 'omg')

    def test_waterfall_with_globals(self):
        md = ModD(dict(shout='uh oh',not_in_modf=True))
        self.assertNotEquals(md.modf.shout, 'uh oh')# not namespaced, no override
        self.assertEquals(md.modf.not_in_modf, True)# global, passed on

    def test_up(self):
        from soppa.internal.tools import Upload
        md = ModD()
        caller_path = here(instance=md)
        upload = Upload('/tmp/a', '/tmp/{self.modf.shout}', instance=md, caller_path=caller_path)
        upload = Upload('/tmp/a', '/tmp/{self.modf}', instance=md, caller_path=caller_path)
        upload = Upload('/tmp/a', '/tmp/{modf}', instance=md, caller_path=caller_path)

class WaterTest(BaseSuite):
    def test_settings_layers(self):
        i = ModC({'modc_hello': 'world', 'external': 'ok'})
        self.assertEqual(i.modc_left, 'left')
        self.assertEqual(i.modc_hello, 'world')
        self.assertEqual(i.external, 'ok')

        i = ModC(ctx={'modc_hello': 'world', 'modc_left': 'right'})
        self.assertEqual(i.modc_left, 'right')
        self.assertEqual(i.modc_hello, 'world')

        i = ModC(dict(modc_left='up'))
        self.assertEqual(i.modc_left, 'up')

class ConfigTest(BaseSuite):
    def test_reading(self):
        instances, values = update_config(Django, path=None, ctx={})
        self.assertTrue(all(k.get_name() in ['django','virtualenv','nodejs'] for k in instances))
        self.assertEquals(values['globals']['path'], u'/srv/www/django/www/')
        self.assertTrue('django' in values['nodejs']['nodejs_binary_dir'])

        instances, values = update_config(Django, path=None, ctx={'project': 'stockticker'})
        self.assertEquals(values['globals']['path'], u'/srv/www/stockticker/www/')
        self.assertTrue('stockticker' in values['nodejs']['nodejs_binary_dir'])
