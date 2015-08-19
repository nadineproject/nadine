# Nadine

This is the Django web project which runs behinds the scenes of coworking spaces.

Most of the action is in the staff application, where you'll find a member tracking and billing system.

## Requirements

* Python (Probably comes with your system otherwise it can be downloaded from their [website](https://www.python.org/downloads/).)
* Virtualenv (install with `pip virtualenv`)
* XCode if you are on Mac OS X 
* Postgresql
* Does not play nice with SQLite

## Handy Installation Instructions

Install the required systems

	apt-get install postgresql postgresql-server-dev-all python-pip python-dev libffi-dev git

Install virtualenv using python pip to work on a sandbox

	pip install virtualenv

Create a virtual environment for the python project

	virtualenv nadine
	cd nadine
	source bin/activate
	
Dowload the nadine source code from github

	git clone https://github.com/nadineproject/nadine.git
	cd nadine

Configure the local settings for your environment

	cp nadine/local_settings.dist nadine/local_settings.py
	vi nadine/local_settings.py

Create a blank database and grant all permissions to whatever account/password combination you want to use.

	psql -c "create database nadinedb"

Install all the requirments 

	pip install -r requirements.txt

Run Django's migrate command and create a superuser.  

	./manage.py migrate
	./manage.py createsuperuser

At this point you can run the server

	./manage.py runserver
	Visit your installation of Nadine at http://127.0.0.1:8000/

You will need to edit the django_sites database in the admin site unless your site is at example.com.

### Running the scheduler

In order to repeatedly execute tasks like checking and sending email, run this command:

    ./manage.py celeryd -B

You will need to run that command as a long lived process.  On linux and other unices, use something like the nohup command.

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
