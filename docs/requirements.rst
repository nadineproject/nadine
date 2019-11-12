Requirements
============

* Python 3.6
* Virtualenv (Virtual environment)
* Homebrew if you are on Mac OS X (https://brew.sh)
* Postgresql

.. important::
  Do not use SQLite.

Base System Installation
------------------------

On Mac OS X

.. code-block:: console

  $ git # If you have not installed it, this will prompt you to download it.
  $ brew update
  $ brew install postgres python3 libffi openssl cairo pango
  $ pip3 install virtualenv

On Ubuntu/Debian

.. code-block:: console

  $ sudo apt-get update
  $ sudo apt-get install git postgresql postgresql-server-dev-all python3-pip python3-dev virtualenv
  $ sudo apt-get install libffi-dev libghc-cairo-dev libghc-pango-dev


Once that is ready, you can start the :doc:`quickstart<quickstart>`
