Nextcloud Django apps made for Nadine Co-Working github project
===============================================================

| This is a simple Nextcloud Django apps for adding user, deactivating user and changing the password of one user on your Nextcloud server.
| This apps works with the Nextcloud API (see `User provisioning API`_).

.. _User provisioning API: https://docs.nextcloud.com/server/15/admin_manual/configuration_user/user_provisioning_api.html

Requirements
~~~~~~~~~~~~

* Python 3.6
* One Django site
* Postgresql
* Nextcloud / Owncloud Server

.. inclusion-stop

Quick install in your project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Download the Nextcloud App source code from Gitlab:

::

   $ git clone https://gitlab.beezim.fr/beezim/nadine.git

Copy the Nextcloud App to your Django site:

::

   $ cd nadine
   $ cp nextcloud path/to/your/django/site

Install all the requirements:

::

   $ pwd
   .../my-django-site
   $ cd nextcloud
   $ pip3 install -r requirements.txt

Then use your favorite text editor to fill the settings:

- Add and fill Nextcloud constants (see back) in the Django site settings:

::

   $ pwd
   .../my-django-site
   $ nano settings.py

- or set it directely in the Nextcloud App settings:

::

   $ pwd
   .../my-django-site/nextcloud
   $ nano settings.py


+-------------------------+---------------------------------+---------------------------------------------------------------------------------+
| Key                     | Default Value                   | Description                                                                     |
+=========================+=================================+=================================================================================+
| NEXTCLOUD_HOST          | cloud.example.com               | Set with the nextcloud server domain                                            |
+-------------------------+---------------------------------+---------------------------------------------------------------------------------+
| NEXTCLOUD_ADMIN         | admin                           | Set with the nextcloud user with admin right (always needed)                    |
+-------------------------+---------------------------------+---------------------------------------------------------------------------------+
| NEXTCLOUD_PASSWORD      | password                        | Set with the nextcloud admin password (APP KEY or user password)                |
+-------------------------+---------------------------------+---------------------------------------------------------------------------------+
| NEXTCLOUD_USE_HTTPS     | True                            | Set False if your nextcloud serveur only use HTTP (port :80)                    |
+-------------------------+---------------------------------+---------------------------------------------------------------------------------+
| NEXTCLOUD_SSL_IS_SIGNED | True                            | Set False if your ssl certificate is not certified                              |
+-------------------------+---------------------------------+---------------------------------------------------------------------------------+
| NEXTCLOUD_USER_GROUP    | None                            | Set the group name where user need to be registered (set None if no group name) |
+-------------------------+---------------------------------+---------------------------------------------------------------------------------+
| NEXTCLOUD_USER_QUOTA    | 100GB                           | Set the quota of the user when he is created (set None for not add quota)       |
+-------------------------+---------------------------------+---------------------------------------------------------------------------------+


- You can change to use your own Alerts Manager in the Nextcloud App settings:

::

   .../my-django-site/nextcloud/settings.py
   ..
   line 3: from .models.alerts import new_membership, ending_membership, changing_membership_password
   ..

- And change the signal name if needed:

::

   .../my-django-site/nextcloud/signals.py
   ..
   line 21: @receiver(new_membership)
   line 64: @receiver(ending_membership)
   line 92: @receiver(changing_membership_password)
   ..


Note
----

This app use the pyocclient library. It is python library shared by owncloud.

Authors
-------

-  **Corentin M.** - *Developer* - `Gitlab Profile`_

.. _Gitlab Profile: https://gitlab.beezim.fr/corentin
