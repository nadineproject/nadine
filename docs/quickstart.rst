Quickstart
==========

Install the :doc:`required systems<requirements>`

Setup the database

.. code-block:: console

  $ sudo su postgres -c "createuser -s $(whoami)"
  $ createdb nadinedb

Create a virtual environment for the python project

.. code-block:: console

  $ virtualenv nadine
  $ cd nadine
  $ source bin/activate


Download the nadine source code from Github

.. code-block:: console

  $ git clone https://github.com/nadineproject/nadine.git
  $ cd nadine

Install all the requirements

.. code-block:: console

  $ pip3 install -r requirements.txt

Run these scripts to setup nadine, install the database, and create your admin user

.. code-block:: console

  $ ./manage.py setup
  $ ./manage.py migrate
  $ ./manage.py createsuperuser

At this point you can run the server

  ``$ ./manage.py runserver``

Visit your installation of Nadine at http://127.0.0.1:8000/
