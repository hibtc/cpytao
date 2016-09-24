# cython: embedsignature=True

cimport pytao.tao_c_interface_mod as clib

from pytao.capture import capture as _capture

import sys
from os import chdir, getcwd


__all__ = [
    'set_init_args',
    'command',
    'capture',
    'scratch_n_lines',
    'scratch_line',

    'chdir',
    'getcwd',
]


def set_init_args(s):
    return clib.tao_c_set_init_args(s.encode('utf-8'))

def command(s):
    return clib.tao_c_command(s.encode('utf-8'))

def scratch_n_lines():
    return clib.tao_c_scratch_n_lines()

def scratch_line(i):
    return clib.tao_c_scratch_line(i).decode('utf-8', 'replace')

def capture(s):
    """Exec command and return the output string."""
    return _capture(command, s)
