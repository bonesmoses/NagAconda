"""
Set up the base testing class for everything.

Currently this includes a base class to test the plugin system, as that's all
NagAconda is at the moment.

"""

import sys
from nose import with_setup
from NagAconda import Plugin

__all__ = ['PlugTest']

class PlugTest:

    def __init__(self):
        self.plugin = None

    def setUp(self):
        """
        Reset argv and initialize a plugin for tests.

        """
        sys.argv = ['test_script']
        self.plugin = Plugin("This is just a test plugin.", "1.2.3")

    def tearDown(self):
        """
        Delete our test plugin for the next iteration.

        """
        self.plugin = None

