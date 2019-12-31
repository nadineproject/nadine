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
