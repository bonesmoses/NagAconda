"""
Test some common usages of the warning/critical threshold settings.
"""

import sys
from nose import with_setup
from NagAconda import Plugin
from test import PlugTest

class TestRanges(PlugTest):
    """
    Test against Nagios's expected range modifiers.

    Nagios's developer docs define several different ways warning and
    critical thresholds should be considered. This class ensures our
    black-box algorithm doesn't inadvertently miss an expected threshold
    boundary or trigger.
    """

    def test_simple_threshold(self):
        """
        Test a simple set of thresholds for state change.

        """
        self.plugin.enable_status('warning', True)
        self.plugin.enable_status('critical', True)
        sys.argv.extend(['-w', '10'])
        sys.argv.extend(['-c', '15'])
        self.plugin.start()

        expected = {7: 'ok', 10: 'ok', 12: 'warning',
                    15: 'warning', 17: 'critical'}

        for (t_val, t_status) in expected.items():
            assert self.plugin.set_value('test', t_val) == t_status

    def test_inverted_threshold(self):
        """
        Test a couple inverted thresholds for state change.

        """
        self.plugin.enable_status('warning', True)
        self.plugin.enable_status('critical', True)
        sys.argv.extend(['-w', '@5:10'])
        sys.argv.extend(['-c', '@15:20'])
        self.plugin.start()

        expected = {3: 'ok', 5: 'warning', 7: 'warning', 10: 'warning',
                    12: 'ok', 15: 'critical', 17: 'critical',
                    20: 'critical', 22: 'ok'}

        for (t_val, t_status) in expected.items():
            assert self.plugin.set_value('test', t_val) == t_status

    def test_range_threshold(self):
        """
        Test a couple range thresholds for state change.

        """
        self.plugin.enable_status('warning', True)
        sys.argv.extend(['-w', '10:15'])
        self.plugin.start()

        expected = {5: 'warning', 10: 'ok', 12: 'ok', 15: 'ok',
                    17: 'warning'}

        for (t_val, t_status) in expected.items():
            assert self.plugin.set_value('test', t_val) == t_status

    def test_multiple_ranges(self):
        """
        Test a couple range thresholds for state change.

        """
        self.plugin.enable_status('warning', True)
        sys.argv.extend(['-w', '10,15'])
        self.plugin.start()

        assert self.plugin.set_value('test', 12, threshold=1) == 'warning'
        assert self.plugin.set_value('test', 12, threshold=2) == 'ok'
        assert self.plugin.set_value('test', 16, threshold=2) == 'warning'

    def test_manual_range(self):
        """
        Test a simple set of manually defined thresholds for state change.

        """
        self.plugin.set_range('warning', 10)
        self.plugin.set_range('critical', 15)
        self.plugin.start()

        expected = {7: 'ok', 10: 'ok', 12: 'warning',
                    15: 'warning', 17: 'critical' }

        for (t_val, t_status) in expected.items():
            print "Testing %s for %s" % (t_val, t_status)
            assert self.plugin.set_value('test', t_val) == t_status


