import unittest, copy, os
from pprint import pprint as pp

from soppa.internal.fmt import fmtkeys

from ..modpack import modpack

class BaseSuite(unittest.TestCase):
    pass

class FormatTest(BaseSuite):
    def test_fmt(self):
        m = modpack()
        self.assertEquals(m._expects({'foo': 1, 'bar': 2}, ['foo']), {'foo': 1})
        m.hello = 'hello'
        self.assertEquals(fmtkeys('{hello} {release.path}'), ['hello','release.path'])
        self.assertEquals(m.fmt('{hello} world'), 'hello world')
        self.assertEquals(m.fmt('hello world'), 'hello world')
        self.assertEquals(m.fmt('{hello} world', hello='bart'), 'bart world')
        self.assertEquals(m.fmt('{hello} {self.hello} world'), 'hello hello world')
        self.assertEquals(m.fmt('{hello} {self.hello} {self.modc}'), 'hello hello {0}'.format(m.modc))

        m.iamjohn = 'John'
        m.iamjoe = '{iamjohn}'
        m.iamnotmary = '{iamjoe}'
        self.assertEqual(m.iamnotmary, 'John')
        self.assertEqual(m.fmt('{iamnotmary}'), 'John')
        self.assertEqual(m.fmt('{imaginarystringhere}'), '')

        self.assertEqual('{} am {}'.format('i', 'me'), 'i am me')

    def test_needs_variable_passing(self):
        m = modpack()
        self.assertEquals(m.modc.soreal, m.modc_soreal)
        self.assertNotEquals(m.modc.soreal, m.soreal)
        self.assertNotEquals(m.modc_soreal, m.soreal)

        self.assertEquals(m.modc_mangle, m.modc.modc_left)
        self.assertEquals(m.modc.mangle, m.modc.modc_left)
        self.assertEquals(m.modc.mangle_self, m.modc.modc_left)
        self.assertEquals(m.modc.__dict__['mangle'], '{modc_left}')
        self.assertEquals(m.modc.__dict__['mangle_self'], '{modc_left}')
