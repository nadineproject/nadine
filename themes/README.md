## Themes

You can override the base templates by activating custom themes.  To do this,
put your theme files in /themes/ and create a symbolic link to the custom theme
called **active**.  

### To Activate
~~~~
cd themes
ln -s theme_you_want active
cd ..
~~~~

### To Deactivate
~~~~
rm themes/active
~~~~

### Theme Settings

All settings constants in a file located at **/themes/active/theme_settings.py**
will be loaded after the settings.py and the local_settings.py.  These constants
are used in the base theme to toggle functionality.

 + FACEBOOK_URL
 + TWITTER_URL
 + YELP_URL
 + ALLOW_PHOTO_UPLOAD
