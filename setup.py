#!/bin/env python
from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):

    user_options = [('pytest-args=', 'a', 'Arguments to pass to py.test')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(['source'] + self.pytest_args)
        sys.exit(errno)


setup(
    name='shellmatic',
    version='0.1.0',

    author='Alexandre Andrade',
    author_email='ama@esss.com.br',

    url='https://github.com/ESSS/shellmatic',

    description = 'Automatic shell configuration with virtualenv activation, environment variables and aliases.',

    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GPLv2',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],

    include_package_data=True,

    install_requires=[
        'ben10',
        'pytest',
    ],
    cmdclass={'test': PyTest},
)
