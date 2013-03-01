#!/usr/bin/env python

from setuptools import setup
import NagAconda

setup(name=NagAconda.__name__,
      version=NagAconda.__version__,
      description="NagAconda is a Python Nagios wrapper.",
      long_description=open('README').read(),
      author='Shaun Thomas',
      author_email='shaun@bonesmoses.org',
      license='New BSD License',
      url='https://github.com/trifthen/NagAconda',
      packages=['NagAconda'],
      tests_require=['nose>=0.11',],
      install_requires=['Sphinx'],
      test_suite = 'nose.collector',
      platforms = 'any',
      classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Documentation',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
      ],
     )
