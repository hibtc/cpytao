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

import numpy as np

from cpymad.madx import ChangeDirectory

from . import rpc


class Tao(object):

    """
    Class for piping in commands to Tao from python and for grabbing Tao output
    """

    def __init__(self, *initargs, **Popen_args):
        self._service, self._process = \
            rpc.TaoClient.spawn_subprocess(**Popen_args)
        self.pipe = self._service.tao_pipe
        self.pipe.set_init_args(' '.join(initargs))
        self._plots = None

    # generic functions to access tao

    def command(self, *command):
        """Send a command to tao without returning the output."""
        self.pipe.command(' '.join(command))

    def capture(self, *command):
        """Send a command to Tao and returns the output string."""
        return self.pipe.capture(' '.join(command))

    def python(self, *command):
        """Execute a python command and get result as list of tuples of strings."""
        self.command('python', *command)
        return [
            _rstrip(self.pipe.scratch_line(n+1).split(';'))
            for n in range(self.pipe.scratch_n_lines())
        ]

    # specialized commands:

    def chdir(self, path):
        """
        Change the directory. Can be used as context manager.

        :param str path: new path name
        :returns: a context manager that can change the directory back
        :rtype: ChangeDirectory
        """
        # Note, that the libmadx module includes the functions 'getcwd' and
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

    # Various functions for getting information from Tao

    def update(self):
        """Recompute curves in tao."""
        self._plots = self.properties('plot_template')

    def plots(self):
        if self._plots is None:
            self.update()
        return self._plots

    def properties(self, *qualname):
        """Get properties as dictionary."""
        return _parse_dict(self.python(*qualname))

    def curve_data(self, name):
        """Get a numpy array of (x,y) value pairs for the specified curve."""
        return _parse_curve(self.python('curve_line', name))

    def curve_names(self, plot):
        """Get the plot specific curve names."""
        graph = self.plots()[plot]
        props = self.properties('graph', plot+graph)
        return [plot+graph+'.'+props[key]
                for key in sorted(props)
                if key.startswith('curve')]

    def plot_data(self, plot):
        return [(self.properties('graph', curve_name),
                 self.properties('curve', curve_name),
                 self.curve_data(curve_name))
                for curve_name in self.curve_names(plot)]

        #color = curve_props['line%color']
        #xlabel = graph_props['x%label']
        #ylabel = graph_props['y%label']



def _parse_dict(data):
    """
    Data is a list of strings for the format "name;TYPE;TF;value."
    The function takes in the data and makes a dictionary of each data and it's value
    """
    def parse_dict_item(fields):
        name, kind = fields[:2]
        if kind == 'STRING':
            value = fields[3]
        elif kind == 'INTEGER':
            value = int(fields[3])
        elif kind == 'REAL':
            value = float(fields[3])
        elif kind == 'LOGICAL':
            value = fields[3] == 'T'
        else:
            value = fields[1]
        return name, value
    return dict(map(parse_dict_item, data))


def _parse_curve(data):
    """Make a numpy array from result of a python command."""
    if not data or data[0][0] == 'INVALID':
        return np.empty((0, 2))
    return np.array([tuple(map(float, item[1:3])) for item in data])


def _rstrip(tup):
    """Strip a trailing empty string from the tuple."""
    return tup[:-1] if tup and tup[-1] == '' else tup
