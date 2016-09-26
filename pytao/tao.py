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

from minrpc.util import ChangeDirectory

from . import rpc


def join_args(args):
    return ' '.join(map(format, args))


class Tao(object):

    """
    Class for piping in commands to Tao from python and for grabbing Tao output
    """

    # TODO: add function to disable automatic curve recomputation

    def __init__(self, *initargs, **Popen_args):
        self._service, self._process = \
            rpc.TaoClient.spawn_subprocess(**Popen_args)
        self.pipe = self._service.tao_pipe
        self.pipe.set_init_args(join_args(initargs))

    # generic functions to access tao

    def command(self, *command):
        """Send a command to tao without returning the output."""
        self.pipe.command(join_args(command))

    def capture(self, *command):
        """Send a command to Tao and returns the output string."""
        return self.pipe.capture(join_args(command))

    def python(self, *command):
        """Execute a python command and get result as list of tuples of strings."""
        self.command('python', '-noprint', *command)
        return [
            self.pipe.scratch_line(n+1).split(';')
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

    # Various functions for getting information from Tao

    def update(self):
        """Recompute curves in tao."""
        # TODO: trigger recomputation of curves
        pass

    def plots(self):
        """Return names of available plots."""
        return self.get_list('plot_list', 't')  # t = templates

    def properties(self, *qualname):
        """Get properties as dictionary."""
        return _parse_dict(self.python(*qualname))

    def get_list(self, *qualname):
        return _parse_list(self.python(*qualname))

    def curve_data(self, name):
        """Get a numpy array of (x,y) value pairs for the specified curve."""
        return _parse_curve(self.python('plot_line', name))

    def curve_names(self, plot):
        """Get the plot specific curve names."""
        graph = self.properties('plot1', plot)['graph[1]']
        props = self.properties('plot_graph', plot+'.'+graph)
        return [plot+'.'+graph+'.'+props[key]
                for key in sorted(props)
                if key.startswith('curve')]

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

    def get_lattice_elements(self, name):
        pass

    def change(self, *what, **data):
        for k, v in data:
            self.tao.command('change', join_args(what), k, '@', v)

    def set(self, *what, **data):
        for k, v in data:
            self.tao.command('set', join_args(what), k, '@', v)


def _parse_dict(data):
    """
    Data is a list of strings for the format "name;TYPE;TF;value."
    The function takes in the data and makes a dictionary of each data and it's value
    """
    if not data or data[0][0] == 'INVALID':
        return {}
    def parse_dict_item(fields):
        name, kind = fields[:2]
        if kind == 'STR':
            value = fields[3]
        elif kind == 'INT':
            value = int(fields[3])
        elif kind == 'REAL':
            value = float(fields[3])
        elif kind == 'LOGIC':
            value = fields[3] == 'T'
        else:
            value = fields[1]
        return name.lower(), value
    return dict(map(parse_dict_item, data))


def _parse_list(data):
    if not data or data[0][0] == 'INVALID':
        return []
    return [v for i, v in data]


def as_list(d):
    """Convert the output of a indexed dict to a list."""
    return [d[k] for k in sorted(d, key=int)]


def _parse_curve(data):
    """Make a numpy array from result of a python command."""
    if not data or data[0][0] == 'INVALID':
        return np.empty((0, 2))
    return np.array([tuple(map(float, item[1:3])) for item in data])


def _rstrip(tup):
    """Strip a trailing empty string from the tuple."""
    return tup[:-1] if tup and tup[-1] == '' else tup
