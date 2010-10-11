# Office Nomads Apps

This is the Django web project which we run behind the scenes to support our coworking space.

Most of the action is in the staff application, where you'll find a member tracking and billing system.

## Requirements

- Django
- South
- MySQL
- mysql-python
- feedparser
- PIL

You may install the python packages via this command:
pip install django south pil mysql-python

## Vague but Helpful Installation Instructions

Set up your Django environment then test that it's up by creating a scratch project and running the Django development server.

Set up MySQL, create a blank database and grant all permissions to whatever account/password combination you want to use for the app.

Copy local_settings.dist to local_settings.py and edit it to reflect your local settings.

Run Django's syncdb and then South's migrate commands.  Both Django and South have excellent documentation, so check there if you run into trouble.

## Installation Notes

 - Many of the required python libraries come in source form and require a gcc to build/install. 
   On OS X this means installing XCode.

 - If you are using a 32bit MySQL pythong will have problems because it defaults to running in 64 bit mode.  
   The error will look like:  blah blah blah "mysql.so: mach-o, but wrong architecture"
   You'll need to get python running in 32 bit mode for this to work.  Run the following:
   export VERSIONER_PYTHON_PREFER_32_BIT=yes

## License & Copyright

Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
