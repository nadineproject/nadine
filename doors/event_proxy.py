#!/usr/bin/env python
import sys
import json
import time
import traceback

from core import Messages, EncryptedConnection

################################################################################
# The Web Application
################################################################################

from flask import Flask, request
webapp = Flask(__name__)

@webapp.route('/event_proxy')
def event_proxy():
    webapp.proxy.send(request.args)
    return "OK"

################################################################################
# Our Proxy Object
################################################################################

class Proxy(object):
    def __init__(self, connection):
        self.connection = connection
    
    def send(self, args):
        event = args.get('event', 'unknown')
        door = args.get('door', 'unknown')
        code = args.get('code', 'unknown')
        print "Incoming Event: %s, Door: %s, Code: %s" % (event, door, code)
        proxy_dict = {'event': event, 'door':door, 'code':code}
        proxy_data = json.dumps(proxy_dict)
        print proxy_data
        response = self.connection.send_message(proxy_data)
        print "Keymaster Response: %s" % response

################################################################################
# Main method 
################################################################################

if __name__ == "__main__":
    # Load our configuration
    with open('gw_config.json', 'r') as f:
        config = json.load(f)
    debug = "-d" in sys.argv

    # Test the connection
    print "Testing connection: %s" % config['KEYMASTER_URL']
    connection = EncryptedConnection(config['ENCRYPTION_KEY'], config['KEYMASTER_URL'])
    response = connection.send_message(Messages.TEST_QUESTION)
    if response == Messages.TEST_RESPONSE:
        print "Keymaster handshake successfull!"
    else:
        raise Exception("Could not connect to Keymaster")
    
    # Create our proxy
    proxy = Proxy(connection)
    webapp.proxy = proxy
    
    # Running on http://localhost:5000/
    print "Starting up Event Proxy..."
    webapp.run(host='0.0.0.0', debug=debug)