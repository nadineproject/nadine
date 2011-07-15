#!/usr/bin/env python
# encoding: utf-8
"""
getArp2.py

Created by Jacob Sayles on 2011-07-12.
Copyright (c) 2011 __MyCompanyName__. All rights reserved.
"""

import sys
import os
import urllib
import urllib2
import base64

USERNAME='admin'
PASSWORD='a2lja3N0YXJ0'
BASE_URL='http://fw/'
ARP_URL='https://fw/diag_arp.php'

def main():
	# create a password manager
	password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

	# Add the username and password.
	# If we knew the realm, we could use it instead of ``None``.
	password_mgr.add_password(None, BASE_URL, USERNAME, base64.b64decode(PASSWORD))

	handler = urllib2.HTTPBasicAuthHandler(password_mgr)

	# create "opener" (OpenerDirector instance)
	opener = urllib2.build_opener(handler)

	# use the opener to fetch a URL
	response = opener.open(ARP_URL)

	# Install the opener.
	# Now all calls to urllib2.urlopen use our opener.
	urllib2.install_opener(opener)
	
	print(response.read())

if __name__ == '__main__':
	main()

