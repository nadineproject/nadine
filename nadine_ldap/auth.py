from django_auth_ldap.backend import LDAPBackend, _LDAPUser
from django.contrib.auth.models import User

class NadineLDAPBackend(LDAPBackend):

    def get_or_create_user(self, username, ldap_user):
        """
        Overriding get_or_create_user to perform our own Django/Nadine User
        lookup.
        django-auth-ldap assumes we would want to create Django/Nadine users if
        they don't exist but we don't want to do this. Instead we throw a
        _LDAPUser.AuthenticationFailed exception.
        """
        try: 
            # Use 'nadine.backends.EmailOrUsernameModelBackend' strategy to
            # look up a user. First by email, then by username.
            if '@' in username:
                user = User.helper.by_email(username)
            else:
                user = User.objects.get(username=username)

        except User.DoesNotExist as e:
            # If we can't match against a user in the database then we bail.
            # LDAP users are created & managed FROM Nadine; we don't want to be
            # creating Django users for existing LDAP accounts.
            user = None

        if (user):
            return (user, user.date_joined)
        else:
            raise _LDAPUser.AuthenticationFailed(
                "User exists in LDAP but doesn't exist in Nadine"
            )
