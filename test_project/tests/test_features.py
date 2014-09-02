import unittest, copy, os
import shutil

from soppa.internal.ingredients import *
from soppa.internal.fmt import fmtkeys, formatloc
from soppa.internal.tools import ObjectDict, Upload
from soppa.internal.runner.default import Runner

# failures, if not importing ahead. Why?
from soppa.internal.packagehandler import Pip
from soppa.operating import operating
# /why

from ..moda import moda
from ..modb import modb
from ..modc import modc
from ..modd import modd
from ..mode import mode
from ..modf import modf
from ..modpack import modpack

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
        m = modpack()
        self.assertFalse(m.isDirty())
        dlog.add('files', m.get_name(), {'diff':'!','source':'foo','target':'bar'})
        self.assertTrue(m.isDirty())

    def test_packages_possibilities(self):
        m = modpack()
        self.assertTrue(m.packman().unique_handlers())

    def test_kwargs_do_not_overwrite_needs(self):
        p = pip(ctx={'virtualenv':{}})
        self.assertTrue(p.has_need('virtualenv'))
        self.assertTrue(p.virtualenv != {})

        p = pip(dict(virtualenv_local_conf_path='/tmp/'))
        self.assertEquals(p.virtualenv.local_conf_path, '/tmp/')
        v = virtualenv()
        with self.assertRaises(AttributeError):
            v.local_conf_path

    def test_variable_namespacing(self):
        ctx = {'host': 'localhost.here'}
        i = graphite(ctx=ctx)
        self.assertEquals(i.host, ctx['host'])

    def test_mlcd(self):
        base_dir = os.getcwd()
        there = here()
        s=Soppa()
        with s.mlcd(os.path.join('../..', 'soppa/supervisor/')):
            self.assertEquals(os.getcwd(), os.path.join(base_dir, 'soppa/supervisor'))
            self.assertEquals(os.getcwd(), os.path.normpath(os.path.join(there, '../../soppa/supervisor/')))

    def test_scoped_env(self):
        p = pip()
        v = virtualenv()
        v.virtualenv_active = True
        self.assertEquals(p.fmt('{virtualenv.virtualenv_active}'), str(v.virtualenv_active))
        self.assertTrue(p.virtualenv.virtualenv_active)
        self.assertTrue(v.virtualenv_active)
        self.assertTrue(p.packages_to)
        self.assertTrue(p.packages_to)
        self.assertTrue(v.pip.packages_to)

    def test_formatting(self):
        self.assertEquals(formatloc('{foo}{bar}', {}), '{foo}{bar}')
        ctx = {'foo':'FOO'}
        self.assertEquals(formatloc('{foo}{bar}', ctx), 'FOO{bar}')
        self.assertEquals(formatloc('{foo}{bar}', ctx, bar='BAR'), 'FOOBAR')

        ctx['foo'] = '{bar}'
        self.assertEquals(formatloc('{foo}', ctx), '{bar}')
        ctx['bar'] = '{town}'
        self.assertEquals(formatloc('{foo}', ctx), '{town}')
        ctx['town'] = 'Helsinki'
        self.assertEquals(formatloc('{foo}', ctx), 'Helsinki')

        self.assertEquals(formatloc('{foo_bar}', {'foo_bar': 'oh'}), 'oh')
        c = {'foo': ObjectDict({'bar': 'oh.oh'})}
        self.assertEquals(formatloc('{foo.bar}', c), 'oh.oh')

        u = Upload('config/statsd_supervisor.conf', '{packages_from}', instance=pip(), caller_path='/tmp/')
        self.assertTrue(all('{' not in k for k in u.args))

        s = 'mkdir -p {basepath}{packages,releases,media,static,dist,logs,config/vassals/,pids,cdn}'
        self.assertTrue('/x/' in formatloc(s, dict(basepath='/x/')))

    def test_formatting_bash(self):
        ctx = {'foo': 'FOO'}
        self.assertEquals(formatloc('{foo} {"print $2"}', ctx), 'FOO {"print $2"}')
        self.assertEquals(formatloc('{foo}', {}), '{foo}')

    def test_formatting_invalid_string(self):
        s = """'ifconfig -a eth1|grep "inet addr"|awk '{gsub("addr:","",$2); print $2}'"""
        self.assertEquals(formatloc(s, {}), s)

    def test_formatting_fun(self):
        def lalafun(kw):
            rs = 100
            return rs
        ctx = {'lala': lalafun}
        r = formatloc('{lala}', ctx)
        self.assertTrue('<function' not in r)
        self.assertEquals(r, '100')

    def test_set_setting(self):
        env.local_deployment = True
        start_str = """hello world\nhawai\n"""
        ff = file({})
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

def overwrite(f, data):
    f.seek(0)
    f.write(data)
    f.truncate()

class PatchTest(BaseSuite):
    def test_env_function(self):
        def _(kw={}):
            return 100
        self.assertEqual(formatloc(_, {}), 100)

class ModuleTest(BaseSuite):

    def test_package(self):
        self.assertEquals(modpack({}).dummy('John'), 'John')

    def test_module_packages(self):
        ma = moda(dict(project='name_moda', modb_project='name_modb_override'))
        mb = modb(dict(project='name_modb'))
        ma.setup()
        self.assertNotEqual(ma.version, mb.version)
        self.assertEquals(ma.project, 'name_moda')
        self.assertEquals(mb.project, 'name_modb')
        self.assertEquals(ma.modb.project, 'name_modb_override')
        ma = moda({'project': 'king'})
        self.assertEquals(ma.project, 'king')

    def test_module_contains_variables_from_dependent_modules(self):
        ma = moda()
        self.assertEquals(ma.var, 'moda')
        self.assertEquals(ma.modb.var, 'modb')
        with self.assertRaises(AttributeError):
            ma.modc.var

    def test_module_variable_waterfall(self):
        """
        child_foo -> self.child.foo/child_foo
        self_child_foo -> self.child.foo/child_foo
        """
        md = modd()
        self.assertEquals(md.modf.modf_shout, 'hello')
        self.assertEquals(md.modf.shout, 'hello')
        md = modd(dict(modf_shout='hello'))
        self.assertEquals(md.modf.modf_shout, 'hello')
        self.assertEquals(md.modf.shout, 'hello')

        md = modd(dict(modd_modf_shout='woof'))
        self.assertEquals(md.modf.modf_shout, 'woof')
        self.assertEquals(md.modf.shout, 'woof')
        md = modd(dict(modf_shout='bark', modd_modf_shout='woof'))
        self.assertEquals(md.modf.modf_shout, 'woof')
        self.assertEquals(md.modf.shout, 'woof')
        md = modd(dict(modd_modf_shout='woof', modf_shout='bark'))
        self.assertEquals(md.modf.modf_shout, 'woof')
        self.assertEquals(md.modf.shout, 'woof')

        md = modd(dict(modd_modf_shout='hello'))
        self.assertEquals(md.modf.shout, 'hello')

        config = dict(
                modd_modf_shout='hello',
                mode_modf_shout='bye',
                some_global='global',)
        md = modd(config)
        me = mode(config)
        self.assertEquals(md.modf.shout, 'hello')
        self.assertEquals(me.modf.shout, 'bye')
        self.assertEquals(me.modf.some_global, 'global')

        mf = modf(dict(modf_shout='omg'))
        self.assertEquals(mf.shout, 'omg')
        self.assertEquals(mf.modf_shout, 'omg')

    def test_waterfall_with_globals(self):
        md = modd(dict(shout='uh oh',not_in_modf=True))
        self.assertNotEquals(md.modf.shout, 'uh oh')# not namespaced, no override
        self.assertEquals(md.modf.not_in_modf, True)# global, passed on

    def test_up(self):
        from soppa.internal.tools import Upload
        md = modd()
        caller_path = here(instance=md)
        upload = Upload('/tmp/a', '/tmp/{self.modf.shout}', instance=md, caller_path=caller_path)
        upload = Upload('/tmp/a', '/tmp/{self.modf}', instance=md, caller_path=caller_path)
        upload = Upload('/tmp/a', '/tmp/{modf}', instance=md, caller_path=caller_path)

class WaterTest(BaseSuite):
    def test_settings_layers(self):
        i = modc({'modc_hello': 'world', 'external': 'ok'})
        self.assertEqual(i.modc_left, 'left')
        self.assertEqual(i.modc_hello, 'world')
        self.assertEqual(i.external, 'ok')

        i = modc(ctx={'modc_hello': 'world', 'modc_left': 'right'})
        self.assertEqual(i.modc_left, 'right')
        self.assertEqual(i.modc_hello, 'world')

        i = modc(dict(modc_left='up'))
        self.assertEqual(i.modc_left, 'up')
