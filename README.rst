pytao
=====

pytao is a python binding for BMad_.

.. _BMad: http://www.lepp.cornell.edu/~dcs/bmad/

Example
-------

.. code-block:: python

    from pytao.pipe import TaoPipe
    pipe = TaoPipe('-lat my_lat.bmad')      # Init with standard command-line switches

    output = pipe.cmd('use var *')          # Issue a command, nothing returned

    output = pipe.cmd_in('show top10')      # Issue a command, capturing stdout
    print(output)                           # Get the stdout of command

    data = pipe.python('help')              # Issue a Tao python command.
    print(data)
