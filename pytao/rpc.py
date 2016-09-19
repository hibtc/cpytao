from __future__ import absolute_import

import sys

from minrpc.client import Client, RemoteProcessCrashed, RemoteProcessClosed


__all__ = [
    'TaoClient',
    'RemoteProcessCrashed',
    'RemoteProcessClosed',
]


class TaoClient(Client):

    @property
    def tao_pipe(self):
        return self.modules['pytao.tao_pipe']
