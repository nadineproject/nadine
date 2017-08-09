Production Setup
================

In a production environment you want a webserver in front of the Django engine
and the preferred one is Nginx.  This will handle all inbound requests, server
your ssl certificate, redirect http requests to https, and serve up static
content in /media and /static.


Create Nadine User
------------------

.. code-block:: console

  $ sudo adduser nadine
  $ sudo su - nadine

Follow all the instructions in :doc:`quickstart<quickstart>` as the nadine user.

Create a few important directories for later.

.. code-block:: console

  $ mkdir -p /home/nadine/logs/
  $ mkdir -p /home/nadine/backups/
  $ mkdir -p /home/nadine/webapp/run/
  $ mkdir -p /home/nadine/webapp/media/
  $ mkdir -p /home/nadine/webapp/static/


Install Nginx and Certbot
-------------------------

.. code-block:: console

  $ sudo apt-get install nginx certbot openssl


Get your LetsEncrypt certificate
--------------------------------

Follow instructions here:  `https://certbot.eff.org/all-instructions/ <https://certbot.eff.org/all-instructions/#debian-9-stretch-nginx>`

If you test your server using the `SSL Labs Server Test <https://www.ssllabs.com/ssltest/>`_ now,
it will only get a B grade due to weak Diffie-Hellman parameters.
We can fix this by creating a new dhparam.pem file and adding it to our server block.

.. code-block:: console

  $ sudo openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048


Copy configuration files in to place
------------------------------------

.. code-block:: console

  $ cd /home/nadine/webapp/nadine/conf
  $ sudo cp etc/nginx/sites-available/nadine /etc/nginx/sites-available/nadine
  $ sudo ln -sf /etc/nginx/sites-available/nadine /etc/nginx/sites-enabled/default
  $ sudo cp etc/nginx/snippets/ssl-nadine.conf /etc/nginx/snippets/
  $ sudo cp etc/nginx/snippets/ssl-params.conf /etc/nginx/snippets/
  $ sudo cp etc/uwsgi/apps-available/nadine.yaml /etc/uwsgi/apps-available/
  $ sudo ln -s /etc/uwsgi/apps-available/nadine.yaml /etc/uwsgi/apps-enabled/

  Edit all configuration files to make sure your domain is correct.


Restart Nginx
-------------

.. code-block:: console

  $ sudo nginx -t
  $ sudo systemctl restart nginx
