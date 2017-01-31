Requirements
============

* Python 2.7
* Virtualenv (Virtual environment)
* Homebrew if you are on Mac OS X (http://brew.sh)
* Postgresql

.. important::
  Do not use SQLite.

Base System Installation
------------------------

On Mac OS X

.. code-block:: console

  $ git # If you have not installed it, this will prompt you to download it.
  $ brew update
  $ brew install postgres python
  $ pip install virtualenv

On Ubuntu/Debian

.. code-block:: console

  $ sudo apt-get update
  $ sudo apt-get install postgresql postgresql-server-dev-all python-pip python-dev virtualenv libffi-dev git


Once that is ready, you can start the :doc:`quickstart<quickstart>`
