from __future__ import absolute_import

import sys

from cpymad._rpc import LibMadxClient, LibMadxService
from cpymad.rpc_util import client
from cpymad.rpc_util.client import RemoteProcessCrashed, RemoteProcessClosed


__all__ = [
    'TaoClient',
    'RemoteProcessCrashed',
    'RemoteProcessClosed',
]


class TaoClient(client.Client):

    @property
    def tao_pipe(self):
        return self.modules['pytao.tao_pipe']

    modules = LibMadxClient.modules


if __name__ == '__main__':
    LibMadxService.stdio_main(sys.argv[1:])
