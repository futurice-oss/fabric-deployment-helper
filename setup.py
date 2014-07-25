from setuptools import setup, find_packages, Command
from setuptools.command.test import test
from setuptools.command.install import install

import os, sys, subprocess

class TestCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        raise SystemExit(
            subprocess.call([sys.executable,
                             '-m',
                             'unittest',
                             'discover',
                             '-p',
                             'test_*.py']))

class InstallCommand(install):
    def run(self):
        install.do_egg_install(self)

base_dir = os.path.dirname(os.path.abspath(__file__))

setup(
    name = "soppa",
    version = "0.0.6",
    description = "Soppa - Sauce for Fabric",
    url = "http://github.com/futurice/soppa",
    author = "Jussi Vaihia",
    author_email = "jussi.vaihia@futurice.com",
    packages = ["soppa"],
    include_package_data = True,
    keywords = 'fabric soppa',
    license = 'BSD',
    install_requires = [
        'Fabric==1.8.3',
        'Jinja2==2.7.2',
        'dirtools==0.2.0',
    ],
    cmdclass = {
        'test': TestCommand,
        #'install': InstallCommand,
    },
)
