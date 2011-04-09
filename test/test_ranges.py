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
                    15: 'warning', 16: 'critical'}

        for (t_val, t_status) in expected.items():
            assert self.plugin.set_value('test', t_val) == t_status

    def test_inclusive_threshold(self):
        """
        Test a couple inclusive thresholds for state change.

        """
        self.plugin.enable_status('warning', True)
        self.plugin.enable_status('critical', True)
        sys.argv.extend(['-w', '@10'])
        sys.argv.extend(['-c', '@15'])
        self.plugin.start()

        expected = {7: 'ok', 10: 'warning', 20: 'critical'}

        for (t_val, t_status) in expected.items():
            assert self.plugin.set_value('test', t_val) == t_status

    def test_range_threshold(self):
        """
        Test a couple range thresholds for state change.

        """
        self.plugin.enable_status('warning', True)
        self.plugin.enable_status('critical', True)
        sys.argv.extend(['-w', '10:15'])
        sys.argv.extend(['-c', '20:25'])
        self.plugin.start()

        expected = {7: 'ok', 12: 'warning', 16: 'ok', 21: 'critical', 26: 'ok'}

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

