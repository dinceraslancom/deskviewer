DeskViewer
---------------------------

A tool that allows remote computer control.
Open source alternative of Teamviewer and Anydesk.

Installing
----------

Install and update using `pip3`_:

.. code-block:: text

    $ pip3 install deskviewer

Python 3.3 and newer.

.. _pip3: https://pip.pypa.io/en/stable/quickstart/


Basic Usage
------------------

Publish the computer and control it remotely.

.. code-block:: bash

    $ deskviewer.publish
    Server Starting 0.0.0.0:8765

    $ deskviewer.connect -h 192.168.x.x
    Connecting Server 192.168.x.x:8765

    or

    $ python -m deskviewer.server
    Server Starting 0.0.0.0:8765

    $ python -m deskviewer.client
    Connecting Server 192.168.x.x:8765



Advanced Usage
-----------------------

Support Basic Authentication

Quality options low and high

serve args :
 * -u --username
 * -p --password
 * -h --host
 * --port

client args :
 * -u --username
 * -p --password
 * -h --host
 * -q --quality ( Options: low, high | default: high)
 * --port

.. code-block:: bash

    $ deskviewer.publish -u user -p pass -h 0.0.0.0 --port 8765
    Server Starting 0.0.0.0:8765


    $ deskviewer.connect -u user -p pass -h 192.168.x.x --port 8765 --quality high
    Connecting Server 192.168.x.x:8765


Support
-------

*   Python 3.3 and above
*   Supports all operating systems

Links
-----

*   License: `MIT License <https://github.com/dinceraslancom/deskviewer/blob/master/LICENSE>`_
*   Code: https://github.com/dinceraslancom/deskviewer
