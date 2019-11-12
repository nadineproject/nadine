Testing
=======

Nadine is written with front-end and back-end tests. You are welcome to run the tests locally. If you do run into any issues, please enter it as an issue `in Github. <https://github.com/nadineproject/nadine/issues>`_

Front-End Testing
-----------------

For Front-End testing, Nadine uses CasperJS which is a 'navigation scripting & testing utility for the PhantomJS (WebKit) and SlimerJS (Gecko) headless browsers, written in Javascript.'

To run these tests, you first must have CasperJS installed and make sure that PhantomJS is installed.

.. code-block:: console

  $ brew install casperjs
  $ phantomjs --version

If you do not have phantomjs, then use brew to install it.

To run all tests:

.. code-block:: console

  $ ./manage.py runserver  #make sure you have the server or running it will error out
  $ casperjs test frontend-testing/tests --username='YOUR_USERNAME' --password='YOUR_PASSWORD' --path='/PAGE_TO_TEST/'

To run a singular test, include the filename after tests/ in the path. In particular, to run tests to verify all links return a status code of 200, we have a test for that. Include a new variable called 'path' and either assign it '/member/' or '/staff/'.

.. code-block:: console

  $ ./manage.py runserver
  $ casperjs test frontend-testing/tests/linktesting.js --username=YOUR_USERNAME --password=PASSWORD --path='/PAGE_TO_TEST/'

Suggested paths:

* '/member/'
* '/member/view/'
* '/staff/'
* '/staff/members/members/'
* '/staff/members/detail/USERNAME'

Some of the tests are checking for a lot of information so it might take a minute or so to run.

Back-End Testing
----------------

Django is wonderful and includes its own ability to run unit tests. According to the docs, 'Django’s unit tests use a Python standard library module: unittest. This module defines tests using a class-based approach.' For more detailed information on Django testing then please see `the documentation <https://docs.djangoproject.com/en/1.10/topics/testing/overview/>`_

To run backend tests, you can be specific or more broad. To run all tests:

``$ ./manage.py test nadine.tests``

To run one specific test, like from the room booking test suite:

``$ ./manage.py test nadine.tests.test_room.RoomTestCase.test_available_straddling``
