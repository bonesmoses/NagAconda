"""
:mod:`Plugin` -- Nagios Plugin Wrapper
======================================

.. module:: Plugin
   :platform: Unix
   :synopsis: Wraps Nagios plugins in a candy coating.
.. moduleauthor:: Shaun Thomas <sthomas@leapfrogonline.com>

The Plugin module provides all the parts necessary to create a simple Nagios
report for a service or host check by removing all that pesky inside
knowledge necessary.  All the classes and methods provided here reduce plugin
creation to a few lines of python unless the plugin is especially complex.

All specifications for this module are obtained from the `Nagios developer
documentation <http://nagiosplug.sourceforge.net/developer-guidelines.html>`_.

Usage
-----

.. code-block:: python

  from NagAconda import Plugin
  from Person import Dude

  feet = Plugin("Plugin to quantify current foot odor.", "1.0")
  feet.add_option('t', 'target', 'Person to check for odor.',
      required=True)

  feet.enable_status('warning')
  feet.enable_status('critical')
  feet.start()

  roommate = Dude(feet.options.target)
  feet.set_value('stench', rommmate.gym_socks())
  feet.set_status_message('Current stench level (%s)' % rommmate.gym_socks())

  feet.finish()

API Specification
-----------------

.. autoclass:: NagAconda.Plugin
   :members: add_option, enable_status, finish, set_value, set_status_message,
             start, unknown_error

"""

__version__ = '0.1.4'
__all__ = ['Plugin']

# We need the option parser primarily to provide an instruction harness to the
# plugins. We'll act as a wrapper and not an extension here because there's
# too much potential namespace pollution due to optparse's attribute creation.
# We also want exit for Nagios specification exit status.

from optparse import OptionParser
import sys

class Plugin:
    """
    This is the primary control class for NagAconda.

    The attributes available here are direct-access to parsed options and
    arguments, not class-level variables.

    .. attribute:: options

       This contains all of the options obtained from the command line for this
       plugin. This includes any options registered by the master class.

    .. attribute:: arguments

       After `start` is called, all command-line options are read, and anything
       left over is placed into this object for further use. Most Nagios
       parsers use explicit option setting, so you might never use this.
    
    """

    def __init__(self, description, version):
        """
        Initialize our Plugin's state.

        The Plugin constructor starts the option parser and fills it with
        the verbose descriptor, as described in the Nagios documentation.
        Warning and Critical thresholds can be enabled later.

        :param description: Paragraphs that describe this plugin.
            Option descriptions are automatically included, as is
            basic usage. This explains the plugin itself.
        :param version: Sets the version of this plugin. Nagios **strongly**
            suggests this is available, so we require it.

        """
        # PUBLIC
        self.options = None
        self.arguments = None

        # PRIVATE
        self.__opt_parser = None   # OptionParser object.
        self.__perf = {}           # Collected performance data.
        self.__req_option = []     # Options considered required for operation.
        self.__started = False     # Has 'start' been called yet?
        self.__exit_status = None  # 'ok', 'warning', or 'critical'.
        self.__exit_message = None # User specified status, filtered.

        # With our variables out of the way, let's start up the option parser
        # with a version and verbose setting, along with a sane usage
        # statement.

        self.__opt_parser = OptionParser(version=version,
            description=description, conflict_handler="resolve")

        self.__opt_parser.add_option('-V', '--version', action='version',
            help="show program's version number and exit"
        )

        self.__opt_parser.add_option('-v', '--verbose', action='count',
            help="Get more verbose status output. "
            "Can be specified up to three times"
        )

        self.__opt_parser.set_usage('%prog')


    def __check_range(self, range_type, name):
        """
        Check a submitted value against warning/critical thresholds

        :param range_type: **warning** or **critical**
        :param name: Name of the performance metric to check against the
            specified range type.

        :raises UserWarning: When the user-specified range is missing the
            threshold necessary to test the targeted variable.

        """
        range_list = getattr(self.options, range_type)
        if not range_list:
            return

        threshold = self.__perf[name]['threshold']
        val = self.__perf[name]['val']

        # Even if the warning/critical thresholds are required, a user may
        # forget to set all necessary ranges. If the ranges are required,
        # exit with a complaint, otherwise just skip the range test.

        if len(range_list) < threshold:
            if range_type not in self.__req_option:
                return
            raise UserWarning, (
                "Please set part %s of the %s threshold!" % (
                threshold, range_type))

        # The option parser should have already split these into proper
        # bottom, top, inclusive, so long as the array element is defined.
        # Perform our range test and set the exit status.

        (bottom, top, inclusive) = range_list[threshold-1]

        if inclusive and val >= bottom and val <= top:
            self.__exit_status = range_type
            self.__perf[name]['state'] = range_type
        elif not inclusive and val > bottom and val < top:
            self.__exit_status = range_type
            self.__perf[name]['state'] = range_type

    def add_option(self, flag, name, helptext, **kwargs):
        """
        Adds a Nagios-style help option to this plugin.

        :param flag: A one-letter shortcut for this option.
        :param name: The full name for this option.
        :param helptext: Instructions for usage of this option.
        :param required: Force option for plugin execution. Default False.
        :type required: True or False
        :param action: What type of storage action should take place for
            this parameter? This is the same as the OptionParser 'action'
            setting. Default is 'store'.
        :type action: Setting string. Default 'store'
        :param callback: When action is `callback`, use specified function.
        :type callback: function reference or None
        :param default: What value to default if unset.
        """
        self.__opt_parser.add_option('-' + flag, '--' + name, help=helptext,
            dest=name, type='string', action=kwargs.get('action'),
            callback=kwargs.get('callback'), default=kwargs.get('default'))

        opt_usage = "-%s %s" % (flag, name.upper())

        if kwargs.has_key('required') and kwargs['required'] is True:
            self.__req_option.append(name)
        else:
            opt_usage = "[%s]" % opt_usage

        opts = self.__opt_parser.get_usage().rstrip("\n")
        self.__opt_parser.set_usage(opts + " " + opt_usage)

    def enable_status(self, status_type, required=False):
        """
        Enable warning or critical exit statuses.

        Nagios requires error levels to be returned by the running
        application to evaluate exit status since the text is indeterminate.
        For Nagios:

         * 0 - Status OK
         * 1 - Plugin is notifying a warning state.
         * 2 - Plugin is notifying of a critical error or state.
         * 3 - Some unknown or unhandled error occurred.
         * other - Nagios will report this as a plugin failure.

        By default, warnings and critical errors are not enabled, in case the
        plugin is just tracking values. This method will turn them on and add
        the proper command-line elements so the user can set them.

        .. note::

           If **warning** or **critical** is enabled and set as required,
           failing to provide them to the plugin will result in an automatic
           exit and presentation of the usage documentation.

        When plugins make use of multiple performance metrics, they may also
        have different scales, and hence warning/critical ranges involved.
        In this case, ranges must be passed by the command-line in
        comma-delimited format.

        :param status_type: Should be either `warning` or `critical`.
        :type status_type: String.
        :param required: Should this threshold be a required option?
        :type required: True or False. Default False.

        """
        try:
            status_type = status_type.lower()
            assert status_type in ('warning', 'critical')
        except (AttributeError, AssertionError):
            self.unknown_error(
                "Status_type can only be one of *warning* or *critical*!")

        self.add_option(status_type[0], status_type,
            "Set the %s notification level." % status_type,
            required=required, action='callback', callback=convert_range)

    def finish(self):
        """
        Prints out all results in a form Nagios understands.

        The process of setting a value through 'set_value' actually applies
        warning and critical threshold checks, so by now, all is over but the
        shouting. This method prints out the status and performance data in a
        manner Nagios will understand.

        """
        try:
            assert self.__started
        except AssertionError:
            self.unknown_error("Start method must be called first!")

        exit_value = 0
        if self.__exit_status == 'warning':
            exit_value = 1
        if self.__exit_status == 'critical':
            exit_value = 2

        # Nagios performance output is values delimited by a space. semicolons
        # separate to val;warn;crit;min;max with the scale included in all
        # output. So, let's get cracking...

        perfs = []

        for (perf_name, perf_dict) in self.__perf.items():

            perfs.append('%s=%s%s;%s;%s;%s;%s' % (
                perf_name, perf_dict['val'], perf_dict['scale'] or '',
                self.options.ensure_value('raw_warning', ''),
                self.options.ensure_value('raw_critical', ''),
                perf_dict['min'] or '', perf_dict['max'] or '')
            )

        perf_string = ''
        if len(perfs) > 0:
            perf_string = '|' + ' '.join(["%s" % item for item in perfs])

        exit_status = self.__exit_status.capitalize()
        if self.__exit_message is not None:
            exit_status += ', %s' % self.__exit_message

        print 'Status ' + exit_status + perf_string
        sys.exit(exit_value)

    def set_value(self, name, val, **kwargs):
        """
        Set a performance measurement for output to Nagios.

        There is theoretically no limit on the number of metrics being tracked
        in Nagios performance output. That said, we strongly recommend reading
        the Nagios developer docs to understand how warning and critical test
        ranges are handled.

        Should a minimum or maximum value be provided here, they will only
        be used to build percentage ranges, and will not otherwise affect
        operation of Nagios.

        This should always be called *after* the **start** method.

        .. note::

           Any value parameter that is not submitted as an numeric type will be
           converted to one so tests work properly.

        :param name: Name of the performance setting.
        :param val: Value observed for this iteration.
        :type val: float
        :param lowest: Minimum possible value for this setting. Optional.
        :type lowest: float or None
        :param highest: Maximum possible value for this setting. Optional.
        :type highest: float or None
        :param scale: The unit of measurement to apply to this value.
            should be a byte measurement (B, KB, MB, GB, TB) or
            a unit of time (s, ms, us, ns), or a percentage (%).
        :type scale: string or None
        :param threshold: Which warning/critical range to target for this
            value? Default 1, since most never use more.
        :type threshold: integer, default 1

        :raises ValueError: When an invalid scale is passed.
        :return string: One of 'ok', 'warning' or 'critical', as to how this
            value compared to the enabled and supplied thresholds.
        """
        try:
            assert self.__started
            val = float(val)
        except AssertionError:
            self.unknown_error("Start method must be called first!")
        except (TypeError, ValueError):
            self.unknown_error("Performance measures must be numeric!")

        val_dict = {'val': val, 'min': None, 'max': None, 'scale': None,
            'threshold': 1, 'state': 'ok'}

        if kwargs.has_key('lowest'):
            val_dict['min'] = float(kwargs.get('lowest'))

        if kwargs.has_key('highest'):
            val_dict['max'] = float(kwargs.get('highest'))

        if kwargs.has_key('threshold'):
            val_dict['threshold'] = kwargs['threshold']

        # Nagios actually understands most byte and time oriented scales.
        # The developer docs also list a counter scale, but we're not certain
        # if any plugin has ever used that. Only accept known scales.

        if kwargs.has_key('scale'):
            scale = kwargs.get('scale')

            if scale.upper() in ('B', 'KB', 'MB', 'GB', 'TB'):
                val_dict['scale'] = scale.upper()
            elif scale.lower() in ('s', 'ms', 'us', 'ns', '%'):
                val_dict['scale'] = scale.lower()
            else:
                raise ValueError("""Scale must be one of: B, KB, MB, GB,
                    TB, s, ms, us, ns, or %.""")

        self.__perf[name] = val_dict

        # We'll use the opportunity to check the status ranges right when the
        # variable is set so we don't have to loop through all of them later.

        if hasattr(self.options, 'warning'):
            self.__check_range('warning', name)

        if hasattr(self.options, 'critical'):
            self.__check_range('critical', name)

        return self.__perf[name]['state']

    def set_status_message(self, message):
        """
        Set a more informational exit string for plugin status.

        By default, NagAconda exits merely with OK, WARNING, or CRITICAL, a
        raw interpretation as applied to provided warning and critical
        thresholds. Clearly this isn't sufficent in many cases where plugins
        know more than merely the metrics being measured. This method is
        provided as a means to manually add textual information to the plugin's
        output that won't interfere with Nagios's parsing of that status.

        Since status may change through the process of the plugin's execution
        several times, or in accordance to the status of several metrics, this
        is provided separately from the 'finish' method.

        .. note::

            This is not the same as verbose Nagios output that can span
            multiple lines. This is just appended to the usual OK / WARNING /
            CRITICAL status reported back to Nagios.

        :param message: Exit status to include in Nagios output. String
            will be filtered to remove characters that may cause Nagios to
            ignore or misinterpret plugin output.
        :type message: string

        """

        # Nagios considers a pipe (|) a split from STATUS MESSAGE and perf
        # data. If we replace it with a space, that should safely render the
        # message safe without risking making it unreadable.

        try:
            assert message is not None
            self.__exit_message = message.replace('|', ' ')
        except (AttributeError, AssertionError):
            self.unknown_error("Status message must be a standard string!")

    def start(self):
        """
        Invokes all preparation steps to retrieve host/service status.

        Starts the actual plugin's work. The Plugin class will start by
        parsing any options so the whole process can short-circuit before
        we do anything important.

        .. note::

          This method may exit directly to the console.

        """
        (self.options, self.arguments) = self.__opt_parser.parse_args()

        for opt_name in self.__req_option:
            if not getattr(self.options, opt_name):
                self.__opt_parser.error("Required option '%s' not set!" %
                    opt_name)

        self.__started = True
        self.__exit_status = 'OK'

    def unknown_error(self, message):
        """
        The Plugin encountered an unexpected error, and must immediately exit.

        The plugin system itself handles all the necessary details when
        processing thresholds, which will take care of OK, WARNING, and
        CRITICAL exit status, but what about UNKNOWN? If some kind of
        unexpected behavior or parameter, or otherwise misbehaving resource
        confuses our plugin, we should immediately stop and reconsider.
        Call this to generate Nagios output with an optional message as to
        why the plugin quit processing.

        This allows 'finish' to continue to function as an expected exit
        point full of processed performance metrics without unnecessary
        error handling/formatting logic.

        :param message: Exit status to include in Nagios output.
        :type message: string

        """
        print 'Status Unknown: ' + message
        sys.exit(3)

def convert_range(option, opt_str, value, parser):
    """
    Convert a warning/critical range into separate testable variables.

    Nagios warning or critical status tests are actually ranges with
    some weird rules. See the developer documentation to see them all,
    but rest assured we've implemented *all* of them.

    :param values: All values currently parsed by OptionParser. We'll
        be adding 'dest' to the pile or extending its values.
    :param dest: **warning** or **critical** range to convert.
    :param value: Range text as passed from the command-line. The
        option parser splits these up if multiple ranges are specified,
        so there's no need to split on a comma and loop.

    """
    # Preserve the original option string for print output.
    parser.values.ensure_value("raw_%s" % option.dest, value)

    for part in value.split(','):

        # If we find a '@' at the beginning of the range, it's inclusive

        inclusive = False

        if part.find('@') == 0:
            inclusive = True
            part = part.lstrip('@')

        # The : separates a max/min range. If it exists, there is at least
        # a minimum. We'll start our ranges at infinity so we don't have to
        # worry about complex testing logic.

        bottom = -float('infinity')
        top = float('infinity')

        if part.find(':') > 0:
            (bottom, top) = part.split(':')
            if top == '':
                top = float('infinity')
            else:
                top = float(top)

            if bottom == '~':
                bottom = -float('infinity')
            else:
                bottom = float(bottom)
        else:
            bottom = float(part)

        # Place bottom, top, and inclusive into a single entry for each found
        # threshold. This lets a user see all possible ranges passed by the
        # user, and select a set based on specification order.

        parser.values.ensure_value(option.dest, []).append([bottom,
            top, inclusive])


if __name__ == "__main__":
    PLUGTEST = Plugin()
    sys.exit(0)

