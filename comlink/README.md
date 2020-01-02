# Comlink

Handle incoming and outgoing emails using mailgun

### Authors

This code consists of many different projects being pulled in from various sources.

 * https://github.com/jsayles
 * https://github.com/jessykate
 * https://github.com/TrevorFSmith
 * https://github.com/hedberg

Derived from:
 * https://github.com/hedberg/django-mailgun-incoming
 * https://github.com/opendoor/django-comlink

### Developer Notes

This project was designed to be able to be a stand-alone module in other projects
although there is one clear violation of that principle.  Nadine users can
have many different email addresses and this system uses that feature to identify
users using the following code:

```python
User.helper.by_email(email)
```

The URLs used for unsubscribing and moderating are also tied to the Nadine application.

### Important settings
The email footer links rely on *settings.SITE_PROTO* and *settings.SITE_DOMAIN* to be set.

Mailgun functionality relies on *settings.MAILGUN_DOMAIN* and *settings.MAILGUN_API_KEY* to be set.  
*settings.MAILGUN_VALIDATION_KEY* is optional if you want to use the v3 validation logic.
