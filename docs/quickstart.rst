Quickstart
==========

Install the :doc:`required systems<requirements>`

Setup the database

.. code-block:: console

  $ sudo su postgres -c "createuser -s $(whoami)"
  $ createdb nadinedb

Download the nadine source code from Github

.. code-block:: console

  $ git clone https://github.com/nadineproject/nadine.git
  $ cd nadine

Install all the requirements

.. code-block:: console

  $ pipenv install --three

Run these scripts to setup nadine, install the database, create your admin user, and compile translations messages:

.. code-block:: console

  $ pipenv shell
  $ ./manage.py setup
  $ ./manage.py migrate
  $ ./manage.py createsuperuser
  $ ./manage.py compilemessages

At this point you can run the development server to make sure everything is set up correctly.

  ``$ ./manage.py runserver``

Visit your installation of Nadine at http://127.0.0.1:8000/
