pytao
=====

pytao is a python binding for tao_.

.. _tao: http://www.lepp.cornell.edu/~dcs/bmad/tao.html


Setup
-----

Build the latest bmad distribution. To enable position independent code in the
static libraries, set

.. code-block:: bash

    export ACC_ENABLE_FPIC=Y

before building the distribution.

Now, from the pytao base folder execute:

.. code-block:: bash

    python setup.py install --bmad-dir=$DIST_BASE_DIR/production

If installing inside a virtualenv, the command ``develop`` is preferred over
``install``.


Environment
-----------

Before running pytao, if you want to access the tao help system, set the
``TAO_DIR`` environment variable, e.g.:

.. code-block:: bash

    export TAO_DIR=$DIST_BASE_DIR/tao


Usage
-----

.. code-block:: python

    from pytao.tao import Tao
    tao = Tao('-lat my_lat.bmad')       # Init with standard command-line switches

    tao.command('use var *')            # Issue a command, nothing returned

    output = tao.capture('show top10')  # Issue a command, capturing stdout
    print(output)                       # Get the stdout of command

    result = tao.python('help')         # Issue a Tao python command.
    print(data)


    import matplotlib.pyplot as plt

    for curve in tao.curve_names('beta'):
        x, y = tao.curve_data(curve).T
        plt.plot(x, y, label=curve)

    plt.legend(loc='upper left')
    plt.show()
