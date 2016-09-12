
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import select


def capture(func, *args, **kwargs):
    return CaptureIO().capture(func, *args, **kwargs)


class CaptureIO(object):

    """
    Utility for redirecting STDIO streams.
    """

    STDOUT = 1

    def __init__(self, fd=STDOUT):
        self.pipe_out, self.pipe_in = os.pipe()
        self.fd = fd

    def capture(self, func, *args, **kwargs):
        with self.enter():
            func(*args, **kwargs)
        return self.read()

    def enter(self):
        """Replace stdout with our write pipe."""
        self.restore = os.dup(self.fd)
        os.dup2(self.pipe_in, self.fd)
        return self

    def exit(self, *args):
        """Restore to terminal."""
        os.dup2(self.restore, self.fd)
        del self.restore

    def __enter__(self):
        pass

    __exit__ = exit

    def more_data(self):
        """Check if we have more to read from the pipe."""
        r, _, _ = select.select([self.pipe_out], [], [], 0)
        return bool(r)

    def read(self):
        out = ''
        while self.more_data():
            out += os.read(self.pipe_out, 1024).decode('utf-8')
        return out
