Themes
============

Nadine's Member application is designed to be changed to better serve each space. Want to include your logo, company color scheme, etc? We tried to make that easy for you.

Currently the Member application is styled to be rather generic and includes the Nadine Logo throughout. What logo is that? That's the cow on the index page of this documentation. You are welcome to stay with this design but we also welcome you to get in the sandbox and make the Member application unique to your coworking space.


Creating a Theme
----------------

It is easy to create your own theme and implement it with the Member application.

Create a new project with the following doc tree:

::

    THEME_NAME/
    ├── theme_settings.py
    ├── static/
    │   ├── css/
    │   │   └──members.css
    │   └── img/
    │   └── js/
    │   └── fonts/
    ├── templates/
    │   ├── members/
    └── .gitignore

Static Folder
^^^^^^^^^^^^^

The static/ folder will contain all of your new styling(css), any particular javascript files you might need, new font files, and images. Here you can include the style sheets for any new CSS framework you might use and/or your own stylesheet.

The **members.css** file will be the most important for your new styling. This is where you can override the stylings from the default theme.

To completely override the layout of a page, you will need to write that page with DTL and HTML and include that in the templates/members folder.

Logo
////

In in the img/ folder, you can include your logos which you will use. If you do not intend to change the HTML then you will need to include two versions of your logo and save them as **logo.png** and **logo-line.png**. The first one to be used on the homepage jumbotron and the other to be part of the top navigation throughout the app.

Theme Settings
^^^^^^^^^^^^^^

In theme_settings/ you can set the local settings for the application. The settings available include things such as the social media URLS, permissions for registration and photo uploads, and others.

For example, a theme_settings file for Office Nomads might look like:

::

  ALLOW_ONLINE_REGISTRATION = False
  ALLOW_PHOTO_UPLOAD = False

  FACEBOOK_URL = "https://www.facebook.com/OfficeNomads"
  TWITTER_URL = 'https://twitter.com/OfficeNomads'
  YELP_URL = 'https://www.yelp.com/biz/office-nomads-seattle-2'
  INSTAGRAM_URL = 'https://www.instagram.com/officenomads/'


Implementing the Theme
^^^^^^^^^^^^^^^^^^^^^^

First, copy your new theme folder into the themes/ folder. Then, in the terminal:

.. code-block:: console

  $ cd themes
  $ ln -s THEME_NAME active

This command tells Nadine to prioritize your theme over the members.css that came with it. Reload the Member App and see how it all looks!
