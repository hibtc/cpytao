# encoding: utf-8
"""
Example:

    >>> from pytao.tao import Tao
    >>> tao = Tao('-lat my_lat.bmad')       # Init with standard command-line switches

    >>> tao.command('use var *')            # Issue a command, nothing returned

    >>> output = tao.capture('show top10')  # Issue a command and return
    >>> print(output)                       # captured stdout

    >>> result = tao.python('help')         # Exec tao python command and
    >>> print(result)                       # return list of string tuples
"""

from __future__ import absolute_import
from __future__ import unicode_literals


import os
import re
import sys
import logging
from collections import namedtuple

# dictionary type that preserves insertion order if not deleting an element.
# (this is technically just an implementation detail of CPython 3.6)
if sys.version_info >= (3, 6):
    OrderedDict = dict
else:
    from collections import OrderedDict

import numpy as np

from minrpc.util import ChangeDirectory
from minrpc.client import Client, RemoteProcessCrashed, RemoteProcessClosed


__all__ = [
    'Tao',
    'RemoteProcessCrashed',
    'RemoteProcessClosed',
]


PARAM_PLACE = {
    # keys according to `who` in `lat_ele1`:
    'parameters':  'element beginning',
    'twiss':       'element beginning',
    'orbit':       'beam_start',
}


Parameter = namedtuple('Parameter', ['name', 'value', 'vary'])


# TODO: close command log when Tao process is stopped
class CommandLog(object):

    """Log command history to a text file."""

    @classmethod
    def create(cls, filename, prefix='', suffix='\n'):
        """Create CommandLog from filename (overwrite/create)."""
        return cls(open(filename, 'wt'), prefix=prefix, suffix=suffix)

    def __init__(self, file, prefix='', suffix='\n'):
        """Create CommandLog from file instance."""
        self._file = file
        self._prefix = prefix
        self._suffix = suffix

    def __call__(self, command):
        """Log a single history line and flush to file immediately."""
        self._file.write(self._prefix + command + self._suffix)
        self._file.flush()


def format_val(value):
    if isinstance(value, float):
        return format(value, '.15e')
    return format(value)


def join_args(args):
    return ' '.join(map(format_val, args))


class Tao(object):

    """
    Class for piping in commands to Tao from python and for grabbing Tao output.

    For now, you should only be using lower level methods to execute tao
    primitive commands or tao python commands.

    For reference of the python commands, see `tao/code/tao_python.f90` in the
    bmad source distribution and try them out yourself!

    The most useful methods are, in that order:

        - :meth:`Tao.command`
        - :meth:`Tao.python`
        - :meth:`Tao.get_list`
        - :meth:`Tao.properties`
        - :meth:`Tao.parameters`
    """

    # TODO: add function to disable automatic curve recomputation

    def __init__(self, *initargs, **Popen_args):
        """
        Initialize new tao process.

            :param initargs: command line arguments for tao
            :param Popen_args: arguments for :func:`subprocess.Popen`.

        The ``initargs`` will automatically be concatenated using white
        spaces, for example, the following two lines are equivalent:

            >>> tao = Tao("-lat girder.lat")
            >>> tao = Tao("-lat", "girder.lat")
        """
        self.debug = Popen_args.pop('debug', False)
        command_log = Popen_args.pop('command_log', None)
        if command_log:
            self.command_log = CommandLog.create(command_log)
        elif self.debug:
            self.command_log = CommandLog(sys.stdout)
        else:
            self.command_log = None
        # stdin=None leads to an error on windows when STDIN is broken.
        # Therefore, we need set stdin=os.devnull by passing stdin=False:
        Popen_args.setdefault('stdin', False)
        Popen_args.setdefault('bufsize', 0)
        self._service, self._process = \
            Client.spawn_subprocess(**Popen_args)
        self.pipe = self._service.modules['pytao.tao_pipe']
        self.pipe.set_init_args(join_args(initargs))
        self.set('global', lattice_calc_on='F')
        self.command('place * none')

    # generic functions to access tao, please use these:

    def command(self, *command):
        """
        Send a command to tao without returning the output.

        For example:

            >>> tao.command("set element bb k1 = 1")
            >>> tao.command("python lat_ele_list 1@0") # (Whoopsie, no output!)

        If you want to retrieve output from a python command, see
        :meth:`Tao.python` instead.

        Multiple arguments are automatically concatenated using whitespaces,
        so the following commands are all equivalent:

            >>> tao.command("set element bb k1 = 1")
            >>> tao.command("set element {} {} = {}".format("bb", "k1", 1))
            >>> tao.command("set", "element", "bb", "k1", "=", 1)
        """
        cmd = join_args(command)
        self._log_command(cmd, "command")
        self.pipe.command(cmd)

    def capture(self, *command):
        """Send a command to Tao and returns the output string."""
        cmd = join_args(command)
        self._log_command(cmd, "capture")
        return self.pipe.capture(cmd)

    def python(self, *command):
        """
        Execute a python command and get result as list of tuples of strings.

            >>> tao.python("lat_ele_list 1@0")
            [[u'0', u'BEGINNING'],
             [u'1', u'BB'],
             [u'2', u'END'],
             [u'3', u'OO']]

            >>> tao.python("lat_ele1 1@0>>0|model twiss")
            [[u'beta_a', u'REAL', u'T', u'  4.4000000000000000E+01'],
             [u'alpha_a', u'REAL', u'T', u' -7.0000000000000000E+00'],
             [u'gamma_a', u'REAL', u'F', u'  1.1363636363636365E+00'],
             ...,
             [u'etap_b', u'REAL', u'T', u'  0.0000000000000000E+00']]

        This only splits the lines and columns of the output into lists, but
        there is no parsing of data types. You get the full info returned from
        the tao python command.

        For many python commands, it may be more convenient to use
        :meth:`Tao.get_list` or :meth:`Tao.properties` instead.
        """
        self.command('python', '-noprint', *command)
        return [
            self.pipe.scratch_line(n+1).split(';')
            for n in range(self.pipe.scratch_n_lines())
        ]

    # Convenience methods for getting info from python commands:

    def get_list(self, *qualname):
        """
        Execute python command and return result as list of strings.

        Similar to :meth:`Tao.python` but avoids the extra index column:

            >>> tao.get_list("lat_ele_list 1@0")
            [u'BEGINNING', u'BB', u'END', u'OO']

        This is often a bit more convenient than :meth:`Tao.python`, but can
        be used only for python commands that return list-like structure.
        """
        return _parse_list(self.python(*qualname))

    def properties(self, *qualname):
        """
        Get properties as dictionary.

        Like :meth:`Tao.python` but more useful for dicts:

            >>> tao.properties("lat_ele1 1@0>>0|model twiss")
            {'beta_a': 44.0,
            u'alpha_a': -7.0,
            u'gamma_a': 1.1363636363636365,
            ...,
            u'etap_b': 0.0}

        This adds a lot of convenience over :meth:`Tao.python`, but can just
        be used for those python commands that return dictionary like
        structures. Note that this doesn't return the "vary" T/F flag.

        (There is also :meth:`Tao.parameters` that works similar to
        :meth:`Tao.properties` but returns a dictionary of :class:`Parameter`
        instead - which knows about the `vary` flag.)
        """
        return self._parse_dict(self.python(*qualname))

    def parameters(self, *qualname):
        """
        Get properties as a dictionary of :class:`Parameter`s.

        Similar to :meth:`Tao.properties` but returns dictionary of
        :meth:`Parameter`:

            >>> params = tao.params("lat_ele1 1@0>>0|model twiss")
            >>> param['beta_a']
            Parameter(name=u'beta_a', value=44.0, vary=True)
            >>> param['beta_a'].vary
            True
        """
        return self._parse_param_dict(self.python(*qualname))

    # specialized commands:

    def chdir(self, path):
        """
        Change the directory. Can be used as context manager.

        :param str path: new path name
        :returns: a context manager that can change the directory back
        :rtype: ChangeDirectory
        """
        # Note, that the tao_pipe module includes the functions 'getcwd' and
        # 'chdir' so it can be used as a valid 'os' module for the purposes
        # of ChangeDirectory:
        return ChangeDirectory(path, self.pipe)

    def read(self, filename, chdir=False):
        """
        READ a lattice file.

        :param str filename: file name with path
        :param bool chdir: temporarily change directory in Bmad process
        """
        if chdir:
            dirname, basename = os.path.split(filename)
            with self.chdir(dirname):
                self.command('read', 'lattice', basename)
        else:
            self.command('read', 'lattice', filename)

    # Various, very specialized functions for interacting with Tao. Use only
    # if you exactly what you're doing:

    def update(self):
        """Recompute curves in tao."""
        self.set('global', lattice_calc_on='T')
        self.set('global', lattice_calc_on='F')

    def plots(self):
        """Return names of available plots."""
        return self.get_list('plot_list', 't')  # t = templates

    def valid_graphs(self):
        return [
            (graph_path, {'plot': plot_info,
                          'graph': graph_info})
            for plot_name  in self.plots()
            for plot_info  in [self.properties('plot1', plot_name)]
            for graph_name in plot_info.get('graph', [])
            for graph_path in [plot_name + '.' + graph_name]
            for graph_info in [self.properties('plot_graph', graph_path)]
            if graph_info.get('curve', [])
            # if  graph_info.get('valid')
        ]

    def curve_data(self, name):
        """Get a numpy array of (x,y) value pairs for the specified curve."""
        return _parse_curve(self.python('plot_line', name))

    def curve_names(self, plot):
        """Get the plot specific curve names."""
        props = self.properties
        return [
            plot+'.'+graph+'.'+curve
            for graph in props('plot1', plot).get('graph', [])
            for curve in props('plot_graph', plot+'.'+graph).get('curve', [])
        ]

    def plot_data(self, plot):
        return [(self.properties('plot_graph', curve_name),
                 self.properties('plot_curve', curve_name),
                 self.curve_data(curve_name))
                for curve_name in self.curve_names(plot)]

        #color = curve_props['line%color']
        #xlabel = graph_props['x%label']
        #ylabel = graph_props['y%label']

    def get_element_data(self, ix_ele, which='model', who='general',
                         universe=1, branch=0):
        return self.properties('lat_ele1 {}@{}>>{}|{} {}'.format(
            universe, branch, ix_ele, which, who
        ))

    def get_element_floor(self, ix_ele, which='model', universe=1, branch=0):
        return _parse_array(self.python('lat_ele1 {}@{}>>{}|{} {}'.format(
            universe, branch, ix_ele, which, 'floor'
        )))

    def get_lattice_elements(self, name):
        pass

    def change(self, *what, **data):
        for k, v in data.items():
            self.command('change', join_args(what), k, '@', v)

    def set(self, *what, **data):
        for k, v in data.items():
            self.command('set', join_args(what), k, '=', v)

    def set_param(self, kind, **kwargs):
        self.change(PARAM_PLACE[kind], **kwargs)

    # internal only, do not use:

    def _log_command(self, command, context):
        if self.command_log:
            self.command_log("{}: {}".format(context, command))

    def _parse_dict(self, data):
        """
        Data is a list of strings for the format "name;TYPE;TF;value."
        The function takes in the data and makes a dictionary of each data and it's value
        """
        if not data or data[0][0] == 'INVALID':
            return OrderedDict()
        return _convert_arrays(map(self._parse_dict_item, data))

    def _parse_dict_item(self, fields):
        name, kind = fields[:2]
        if kind == 'STR':
            value = fields[3]
        elif kind == 'INT':
            value = int(fields[3])
        elif kind == 'REAL':
            value = float(fields[3])
        elif kind == 'LOGIC':
            value = fields[3] == 'T'
        elif kind == 'ENUM':
            value = self._create_enum_value(name, fields[3])
        else:
            value = fields[1]
        return name.lower(), value

    def _create_enum_value(self, name, value):
        return value

    def _parse_param_dict(self, data):
        if not data or data[0][0] == 'INVALID':
            return OrderedDict()
        # TODO: what to do for lists?
        # - currently converted to: [Parameter]
        # - should it be rather: Parameter([])?
        return _convert_arrays(map(self._parse_param, data))

    def _parse_param(self, fields):
        key, value = self._parse_dict_item(fields)
        vary = fields[2] == 'T'
        return key, Parameter(key, value, vary)


RE_ARRAY = re.compile(r'^(.*)\[(\d+)\]$')

def _convert_arrays(items):
    """
    Convert sequential data in properties to lists.

    The command

        Tao> python plot_graph beta.g

    contains the items

        (num_curves, 2)
        (curve[1], a)
        (curve[2], b)

    which will be transformed to a single item:

        (curve, [a, b])
    """
    result = OrderedDict()
    arrays = set()
    i0 = {}
    for key, val in items:
        m = RE_ARRAY.match(key)
        if m:
            name, index = m.groups()
            l = result.setdefault(name, [])
            l.append(val)
            arrays.add(name)
            # consistency check:
            if len(l) == 1:
                i0[name] = int(index)
            elif int(index) != len(l):
                logging.getLogger(__name__).warn(
                    "Inconsistent array order: Got index {}, expected {}.\n"
                    "Please report this at https://github.com/hibtc/pytao/issues."
                    .format(index, len(l)))
        else:
            result[key] = val
    for name in arrays:
        count = int(result.pop('num_'+name+'s', 0))
        # consistency check:
        if count != len(result[name]):
            logging.getLogger(__name__).warn(
                "Inconsistent array length: adverised as {}, got only {} items.\n"
                "Please report this at https://github.com/hibtc/pytao/issues."
                .format(count, len(result[name])))
    return result


def _parse_list(data):
    if not data or data[0][0] == 'INVALID':
        return []
    return [v for i, v in data]


def as_list(d):
    """Convert the output of a indexed dict to a list."""
    return [d[k] for k in sorted(d, key=int)]


def _parse_array(data, shape=(0, 0)):
    """Make a numpy array from result of a python command."""
    if not data or data[0][0] == 'INVALID':
        return np.empty(shape)
    return np.array([tuple(map(float, row)) for row in data])


def _parse_curve(data):
    """Make a numpy array from result of a python command."""
    return _parse_array(data, (0, 3))[:,1:]


def _rstrip(tup):
    """Strip a trailing empty string from the tuple."""
    return tup[:-1] if tup and tup[-1] == '' else tup
