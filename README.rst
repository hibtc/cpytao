pytao
=====

pytao is a python binding for BMad_.

.. _BMad: http://www.lepp.cornell.edu/~dcs/bmad/

Example
-------

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
