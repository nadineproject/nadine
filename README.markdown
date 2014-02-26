# Nadine

This is the Django web project which runs behinds the scenes of coworking spaces.

Most of the action is in the staff application, where you'll find a member tracking and billing system.

## Handy Installation Instructions

Requires Django 1.5 or above.  Note, we didn't do the full Django 1.3 to Django 1.4 upgrade yet so there are some timezone issues that need to be worked out.

Set up your Django environment then test that it's up by creating a scratch project and running the Django development server.

Set up PostgreSQL, create a blank database and grant all permissions to whatever account/password combination you want to use for the app.

	git clone git://github.com/nadineproject/nadine.git
	cd nadine
	pip install -r requirements.txt

Copy local_settings.dist to local_settings.py and edit it to reflect your local settings. 

Run Django's syncdb and then South's migrate commands.  
(Currently creating a superuser before running migrate is broken; when prompted to create one, choose no.
After running the <code>migrate</code> command, run <code>./manage.py createsuperuser</code>.)

    ./manage.py syncdb --all
    ./manage.py migrate --fake

Now run the tests to make certain that everthing is installed:

    ./manage.py test staff interlink

Both Django and South have excellent documentation, so check there if you run into trouble.

At this point you will need to populate the django_sites database. We will assume you only have Nadine in the database you have created.

	./manage.py shell
	>>> from django.contrib.sites.models import Site
	>>> newsite = Site(name="Nadine",domain="nadine.com")
	>>> newsite.save()
	Ctrl+D

At this point you can run the server

    ./manage.py runserver 0.0.0.0:8000

And visit your installation of Nadine at http://127.0.0.1:8000/

### Running the scheduler

In order to repeatedly execute tasks like checking and sending email, run this command:

    ./manage.py celeryd -B

You will need to run that command as a long lived process.  On linux and other unices, use something like the nohup command.

## Installation Notes

 - Many of the required python libraries come in source form and require a gcc to build/install. 
   On OS X this means installing XCode.

 - If you are using a 32bit MySQL python will have problems because it defaults to running in 64 bit mode.  
   The error will look like:  blah blah blah "mysql.so: mach-o, but wrong architecture"
   You'll need to get python running in 32 bit mode for this to work.  Run the following:
   export VERSIONER_PYTHON_PREFER_32_BIT=yes 

 - On OS X versions *before* Lion when using a virtualenv, you should remove the 64 python altogether like so:
   $ mv .../virtualenvs/nadine/bin/python .../virtualenvs/nadine/bin/python.old
   $ lipo -remove x86_64 .../virtualenvs/nadine/bin/python.old -output .../virtualenvs/nadine/bin/python

 - If you are getting a "flat namespace" error when you try to do a syncdb then you most likely are running OS X 10.6
   and it's trying to run python in 64bit mode.  Do the following:
   $ defaults write com.apple.versioner.python Prefer-32-Bit -bool yes

# Interlink (mailing lists) notes:

In the interest of shipping more quickly, we have made certain assumptions about the interlink mailing lists which may or may not suit everyone's needs.

- the reply-to address for mail from a list is the original sender, not the entire list
- attachments are neither saved nor sent to the list, but a removal note is appended to the message
- incoming messages are parsed for a single text message and a single html message (not multiple MIME messages)
- you can set the frequency of mail fetching by changing the value in CELERYBEAT_SCHEDULE in your settings.py or local_settings.py
- loops and bounces are silently dropped
- any email sent to a list which is not in a subscriber's user or membership record is moderated
- the sender of a message receives a copy of the message like any other subscriber

## License & Copyright

Copyright 2010 Office Nomads LLC ([http://www.officenomads.com/](http://www.officenomads.com/)) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.

You may obtain a copy of the License at [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

See the License for the specific language governing permissions and limitations under the License.
