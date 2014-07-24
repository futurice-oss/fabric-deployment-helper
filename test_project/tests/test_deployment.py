import unittest, copy, os
import shutil

class BaseSuite(unittest.TestCase):
    def test_hello(self):
        self.assertEquals(1,1)
