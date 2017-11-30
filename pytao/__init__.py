# encoding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals

__title__ = 'pytao'
__version__ = '0.0.0'

__summary__ = 'Python binding to tao shared object'
__uri__ = 'https://github.com/hibtc/pytao'

__author__ = 'Thomas Gläßle'
__author_email__ = 't_glaessle@gmx.de'
__support__ = __author_email__

__license__ = 'GPLv3+'
__copyright__ = 'Copyright 2016 HIT Betriebs GmbH'

__credits__ = """
pytao is developed for HIT Betriebs GmbH.

Created by:

- Thomas Gläßle <t_glaessle@gmx.de>

With the help of:

- David Carl Sagan <dcs16@cornell.edu>
- Christopher Earl Mayes <christopher.mayes@cornell.edu>

Special thanks to my supervisors for their help and support:

- Rainer Cee
- Andreas Peters
"""

__classifiers__ = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Topic :: Scientific/Engineering :: Physics',
]

def get_copyright_notice():
    from pkg_resources import resource_string
    return resource_string('madqt', 'COPYING.txt').decode('utf-8')
