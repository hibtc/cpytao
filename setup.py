"""
Installation script for pytao.

Usage:
    python setup.py install
"""

from setuptools import setup, Extension
from distutils.util import convert_path, get_platform
from distutils import sysconfig

import sys
import os


# setuptools.Extension automatically converts all '.pyx' extensions to '.c'
# extensions if detecting that neither Cython nor Pyrex is available. Early
# versions of setuptools don't know about Cython. Since we don't use Pyrex
# in this module, this leads to problems in the two cases where Cython is
# available and Pyrex is not or vice versa. Therefore, setuptools.Extension
# needs to be patched to match our needs:
try:
    # Use Cython if available:
    from Cython.Build import cythonize
except ImportError:
    # Otherwise, always use the distributed .c instead of the .pyx file:
    def cythonize(extensions):
        def pyx_to_c(source):
            return source[:-4]+'.c' if source.endswith('.pyx') else source
        for ext in extensions:
            ext.sources = list(map(pyx_to_c, ext.sources))
            missing_sources = [s for s in ext.sources if not os.path.exists(s)]
            if missing_sources:
                raise OSError(('Missing source file: {0[0]!r}. '
                               'Install Cython to resolve this problem.')
                              .format(missing_sources))
        return extensions
else:
    orig_Extension = Extension
    class Extension(orig_Extension):
        """Extension that *never* replaces '.pyx' by '.c' (using Cython)."""
        def __init__(self, name, sources, *args, **kwargs):
            orig_Extension.__init__(self, name, sources, *args, **kwargs)
            self.sources = sources


def main(argv):
    """Execute setup."""
    fix_distutils_sysconfig_mingw()
    setup_args = get_setup_args(sys.argv)
    setup(**setup_args)


def read_file(path):
    """Read a file in binary mode."""
    with open(convert_path(path), 'rb') as f:
        return f.read()


def exec_file(path):
    """Execute a python file and return the `globals` dictionary."""
    namespace = {}
    exec(read_file(path), namespace, namespace)
    return namespace


def get_long_description():
    """Compose a long description for PyPI."""
    long_description = None
    try:
        long_description = read_file('README.rst').decode('utf-8')
        long_description += '\n' + read_file('COPYING.rst').decode('utf-8')
        long_description += '\n' + read_file('CHANGES.rst').decode('utf-8')
    except (IOError, UnicodeDecodeError):
        pass
    return long_description


def fix_distutils_sysconfig_mingw():
    """
    When using windows and MinGW, in distutils.sysconfig the compiler (CC) is
    not initialized at all, see http://bugs.python.org/issue2437. The
    following manual fix for this problem may cause other issues, but it's a
    good shot.
    """
    if sysconfig.get_config_var('CC') is None:
        sysconfig._config_vars['CC'] = 'gcc'


def get_setup_args(argv):
    extension_args = get_extension_args(argv)
    long_description = get_long_description()
    metadata = exec_file('pytao/__init__.py')
    return dict(
        name=metadata['__title__'],
        version=metadata['__version__'],
        description=metadata['__summary__'],
        long_description=long_description,
        author=metadata['__author__'],
        author_email=metadata['__author_email__'],
        url=metadata['__uri__'],
        classifiers=metadata['__classifiers__'],
        packages = [
            "pytao",
        ],
        ext_modules = cythonize([
            Extension('pytao.tao_pipe',
                      sources=["pytao/tao_pipe.pyx"],
                      **extension_args),
        ]),
        install_requires=[
            'setuptools',
            'minrpc',
        ],
        package_data={
            'pytao': [
                'COPYING.txt'
            ]
        }
    )


def remove_arg(args, opt):
    """
    Remove all occurences of ``--PARAM=VALUE`` or ``--PARAM VALUE`` from
    ``args`` and return the corresponding values.
    """
    iterargs = iter(args)
    result = []
    remain = []
    for arg in iterargs:
        if arg == opt:
            result.append(next(iterargs))
        elif arg.startswith(opt + '='):
            result.append(arg.split('=', 1)[1])
        else:
            remain.append(arg)
    args[:] = remain
    return result


def get_extension_args(argv):
    """Get arguments for C-extension (include pathes, libraries, etc)."""
    # Let's just use the default system headers:
    include_dirs = []
    library_dirs = []
    # Parse command line option: --bmad-dir=/path/to/bmad_installation. We could
    # use build_ext.user_options instead, but then the --bmad-dir argument can
    # be passed only to the 'build_ext' command, not to 'build' or 'install',
    # which is a minor nuisance.
    base_dir = os.environ['DIST_BASE_DIR']
    fallback = [os.path.join(base_dir, 'production'),
                os.path.join(base_dir, 'debug')]
    fallback = list(filter(os.path.isdir, fallback))
    bmad_dir, = remove_arg(argv, '--bmad-dir') or [fallback[0]]
    bmad_dir = prefix = os.path.expanduser(bmad_dir)
    lib_path_candidates = [os.path.join(prefix, 'lib'),
                           os.path.join(prefix, 'lib64')]
    include_dirs.append(os.path.join(prefix, 'include'))
    library_dirs.extend(filter(os.path.isdir, lib_path_candidates))
    plot_lib = os.environ.get('ACC_PLOT_PACKAGE')
    if plot_lib == 'pgplot':
        plot_libs = ['pgplot']
        ext_plot_libs = ['X11']
    elif plot_lib == 'plplot':
        plot_libs = [
            'plplotcxx',
            'plplotf95',
            'plplot',
            'csirocsa',
            'qsastime',
        ]
        ext_plot_libs = [
            'pangocairo-1.0',
            'cairo',
            'X11',
        ]
    elif plot_lib == 'none':
        plot_libs = []
        ext_plot_libs = []
    else:
        raise RuntimeError(
            "Unknown plot mode. $ACC_PLOT_PACKAGE must be 'plplot', 'pgplot' or 'none'.")
    # order matters:
    internal_libs = [
        'tao',
        'bmad',
        'sim_utils',
        'forest',
        'xrlf03',
        'xrl',
        'xsif',
        'fgsl',
        'gsl',
        'gslcblas',
        'recipes_f-90_LEPP',
    ] + plot_libs + [
        'lapack95',
        'lapack',
        'blas',
    ]
    external_libs = ext_plot_libs + [
        'readline',
        'gfortran',
    ]
    # required libraries
    if get_platform() == "win32" or get_platform() == "win-amd64":
        # TODO: actually try this on windows
        pass
    # NOTE: pass 'extra_link_args' in favor of 'libraries' in order to be able
    # to insert 'static/dynamic' hints.
    # NOTE: Apple's clang linker doesn't support mixing static/dynamic linking
    # using `-Bdynamic`, `-Bstatic` hints, therefore we have to specify the
    # full pathname:
    link_args = []
    link_args += [os.path.join(bmad_dir, 'lib', 'lib'+lib+'.a') for lib in internal_libs]
    link_args += ['-l'+lib for lib in external_libs]
    # Common arguments for the Cython extensions:
    return dict(
        libraries=[],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        runtime_library_dirs=library_dirs,
        extra_link_args=link_args,
        extra_compile_args=['-std=gnu99'],
    )


if __name__ == '__main__':
    main(sys.argv)
