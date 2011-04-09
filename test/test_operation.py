"""
Test how the output matches what Nagios expects.
"""

import sys
from nose import with_setup
from NagAconda import Plugin
from test import PlugTest

class TestOperation(PlugTest):
    """
    Test command output for Nagios expectations

    Nagios expects a very specific form of output from plugins. NagAconda
    strives to fit exactly what the developer docs specify, which these
    tests verify.
    """

    def test_ok_status(self):
        """
        Check the exit status for 'ok' readings.

        For Nagios, an 'ok' status is equal to 0.

        """
        self.plugin.enable_status('warning', True)
        sys.argv.extend(['-w', '10'])

        try:
            self.plugin.start()
            self.plugin.set_value('foo', 9)
            self.plugin.finish()
        except SystemExit, e:
            assert e.code == 0
        else:
            assert False

    def test_warning_status(self):
        """
        Check the exit status for 'warning' readings.

        For Nagios, a 'warning' status is equal to 1.

        """
        self.plugin.enable_status('warning', True)
        sys.argv.extend(['-w', '10'])

        try:
            self.plugin.start()
            self.plugin.set_value('foo', 11)
            self.plugin.finish()
        except SystemExit, e:
            assert e.code == 1
        else:
            assert False

    def test_critical_status(self):
        """
        Check the exit status for 'critical' readings.

        For Nagios, a 'critical' status is equal to 2.

        """
        self.plugin.enable_status('warning', True)
        self.plugin.enable_status('critical', True)
        sys.argv.extend(['-w', '10'])
        sys.argv.extend(['-c', '15'])

        try:
            self.plugin.start()
            self.plugin.set_value('foo', 16)
            self.plugin.finish()
        except SystemExit, e:
            assert e.code == 2
        else:
            assert False

    def test_unknown_status(self):
        """
        Check the exit status for erroneous readings.

        For Nagios, an 'unknown' status is equal to 3 or greater. Luckily,
        we can just invoke unknown_error to do this.

        """
        try:
            self.plugin.unknown_error('Something Explodey happened')
        except SystemExit, e:
            assert e.code == 3
        else:
            assert False


