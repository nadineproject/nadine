Nginx Setup
===========

In a production environment you want a webserver in front of the Django engine
and the preferred one is Nginx.  This will handle all inbound requests, server
your ssl certificate, redirect http requests to https, and serve up static
content in /media and /static.

Install Nginx and Certbot
-------------------------

.. code-block:: console

  $ sudo apt-get install nginx certbot openssl

Get your LetsEncrypt certificate
--------------------------------

Follow instructions here:  https://certbot.eff.org/all-instructions/

If you test your server using the `SSL Labs Server Test <https://www.ssllabs.com/ssltest/>`_ now,
it will only get a B grade due to weak Diffie-Hellman parameters.
We can fix this by creating a new dhparam.pem file and adding it to our server block.

.. code-block:: console

  $ sudo openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048
