Themes
============

Nadine's Member application is designed to be changed to better serve each space. Want to include your logo, company color scheme, etc? We tried to make that easy for you.

Currently the Member application is styled to be rather generic and includes the Nadine Logo throughout. What logo is that? That's the cow on the index page of this documentation. You are welcome to stay with this design but we also welcome you to get in the sandbox and make the Member application unique to your coworking space.


Creating a Theme
----------------

It is easy to create your own theme and implement it with the member application.

Create a new project with the following doc tree:

::

    theme/
    ├── theme_settings.py
    ├── static/
    │   ├── css/
    │   │   └──members.css
    │   └── img/
    │   └── js/
    │   └── fonts/
    └── .gitignore

Static Folder
^^^^^^^^^^^^^

The static/ folder will contain all of your new styling(css), any particular javascript files you might need, new font files, and images. Here you can include the style sheets for any new CSS framework you might use and/or your own stylesheet.

The members.css file will be the most important for your new styling. This is where you can override the stylings from the default theme.

In in the img/ folder, you can include your logos which you will use. If you do not intend to change the HTML then you will need to include two versions of your logo. One to be used on the homepage jumbotron and another to be part of the top navigation throughout the app.

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


For More info, dance.
