#!/usr/bin/env python
import threading
import queue

import sys
import json
import time
import traceback

import cherrypy

from core import Messages, EncryptedConnection, DoorEventTypes

################################################################################
# The Web Application
################################################################################
class EventProxy(threading.Thread):
    def __init__(self, queue, special_codes, doors, users, connection):
        threading.Thread.__init__(self)
        self.queue = queue
        self.special_codes = special_codes
        self.doors = doors
        self.users = users
        self.connection = connection

    @cherrypy.expose
    def index(self):
        return "I'm the event proxy!"

    # This is the one that takes the event data from the doors
    @cherrypy.expose
    def event_proxy(self, **args):
        # event = args.get('event', 'unknown')
        # door = args.get('door', 'unknown')
        # code = args.get('code', 'unknown')
        # print("Incoming Event: %s, Door: %s, Code: %s" % (event, door, code))
        proxy_dict = self.event_for_keymaster_from_hid_args(args)

        proxy_data = json.dumps(proxy_dict)
        print(proxy_data)
        response = self.connection.send_message(proxy_data)
        print(("Keymaster Response: %s" % response))
        return "Here's where I would actually process the stuff"

    def run(self):
        cherrypy.quickstart(self)

    def event_for_keymaster_from_hid_args(self, args):
        #Args that come from the reader: firstname, lastname, cardnumber, doorname, action
        if args["action"] == "GRANTED":
            event_type = DoorEventTypes.GRANTED
        elif args["action"] == "DENIED":
            event_type = DoorEventTypes.DENIED
        else:
            event_type = DoorEventTypes.UNKNOWN
        new_args = {
            "event_type": event_type,
            "event_description": str(args),
        }
        if "doorname" in args and args["doorname"] in self.doors:
            new_args["door_id"] = self.doors[args["doorname"]]
        if "lastname" in args and args["lastname"] in self.users:
            new_args["user_id"] = self.users[args["lastname"]]
        if "cardnumber" in args:
            new_args["code"] = args["cardnumber"]
        return new_args

################################################################################
# Main method
################################################################################

if __name__ == "__main__":
    # Load our configuration
    with open('gw_config.json', 'r') as f:
        config = json.load(f)
    debug = "-d" in sys.argv

    # Test the connection
    print(("Testing connection: %s" % config['KEYMASTER_URL']))
    connection = EncryptedConnection(config['ENCRYPTION_KEY'], config['KEYMASTER_URL'])
    response = connection.send_message(Messages.TEST_QUESTION)
    if response == Messages.TEST_RESPONSE:
        print("Keymaster handshake successfull!")
    else:
        raise Exception("Could not connect to Keymaster")

    queue = queue.PriorityQueue()

    doors = {'FrontDoor': 1}
    users = {'mike': 1}
    special_codes = ['abc']

    # Create our proxy
    proxy = EventProxy(queue, special_codes, doors, users, connection)
    proxy.setDaemon(True)
    proxy.start()

    while True:
        time.sleep(.1)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
