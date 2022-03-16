"""
:mod:`NagAconda` -- Python Nagios Integration
=============================================

Nagios has been around for quite some time, but producing output it can
consume is something of a black art. Only the plugin documentation actually
explains what all the extra semicolons or extended formatting even means.

This is especially onerous when performance consuming add-ons expect a
specific structure before operating properly. This package strives to
greatly simplify the process of actually generating Nagios output.

.. automodule:: NagAconda.plugin

"""

__version__ = "0.3.5"

import sys
if sys.version_info[0] > 2:
    from .Plugin import Plugin
else:
    from Plugin import Plugin

