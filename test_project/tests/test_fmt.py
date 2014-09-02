import unittest, copy, os
from pprint import pprint as pp

from ..modpack import ModPack

class BaseSuite(unittest.TestCase):
    pass

class FormatTest(BaseSuite):
    def test_fmt(self):
        m = ModPack()
        self.assertEquals(m._expects({'foo': 1, 'bar': 2}, ['foo']), {'foo': 1})
        m.hello = 'hello'
        self.assertEquals(m.fmtkeys('{hello} {path}'), ['hello','path'])
        self.assertEquals(m.fmt('{hello} world'), 'hello world')
        self.assertEquals(m.fmt('hello world'), 'hello world')
        self.assertEquals(m.fmt('{hello} world', hello='bart'), 'bart world')
        self.assertEquals(m.fmt('{hello} {self.hello} world'), 'hello hello world')
        self.assertEquals(m.fmt('{hello} {self.hello} {self.modc}'), 'hello hello {0}'.format(m.modc))

        m.iamjohn = 'John'
        m.iamjoe = '{iamjohn}'
        m.iamnotmary = '{iamjoe}'
        self.assertEqual(m.iamnotmary, '{iamjoe}')
        self.assertEqual(m.fmt('{iamnotmary}'), 'John')
        m.strict_fmt = False
        self.assertEqual(m.fmt('{imaginarystringhere}'), '')
        m.strict_fmt = True
        with self.assertRaises(KeyError):
            self.assertEqual(m.fmt('{imaginarystringhere}'), '')

        self.assertEqual('{} am {}'.format('i', 'me'), 'i am me')

    def test_fmt_returns_non_strings_as_is(self):
        m = ModPack()
        self.assertEqual(m.fmt(True), True)

    def test_needs_variable_passing(self):
        m = ModPack()
        self.assertEquals(m.modc.soreal, m.modc_soreal)
        self.assertNotEquals(m.modc.soreal, m.soreal)
        self.assertNotEquals(m.modc_soreal, m.soreal)

        # modc inherits values from modpack into its own namespace
        # modpack.modc_mangle => (modc) self.mangle
        self.assertEquals(m.modc_mangle, m.modc.modc_left)
        self.assertEquals(m.modc.mangle, m.modc.modc_left)
        self.assertEquals(m.modc.mangle_self, m.modc.modc_left)
        self.assertEquals(m.modc.__dict__['mangle'], m.modc.modc_left)
        self.assertEquals(m.modc.__dict__['mangle_self'], m.modc.modc_left)

        self.assertEquals(m.modc.voodoo(), False)

        self.assertEquals(m.project, 'modpack')

    def test_resolution_order(self):
        m = ModPack()
        self.assertEquals(m.project, m.get_name())
        self.assertEquals(m.modc.project, m.modc.get_name())

        m = ModPack(dict(
            project='foo',
            modc_project='bar',
            ))
        self.assertEquals(m.project, 'foo')
        self.assertEquals(m.fmt('{project}'), 'foo')
        self.assertEquals(m.modc.project, 'bar')
        self.assertEquals(m.modc.modc_project, 'bar')
        m.modc.project = 'omg'
        self.assertEquals(m.modc.project, 'omg')
