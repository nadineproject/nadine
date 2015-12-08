#!/usr/bin/env python
import sys
import json
import time
import traceback

from core import Messages, EncryptedConnection, Gatekeeper

class GatekeeperApp(object):
    def run(self, initialSync):
        try:
            print "Starting up Gatekeeper..."
            connection = EncryptedConnection(config['ENCRYPTION_KEY'], config['KEYMASTER_URL'])
            gatekeeper = Gatekeeper(connection)
            
            # Test the connection
            response = connection.send_message(Messages.TEST_QUESTION)
            if response == Messages.TEST_RESPONSE:
                print "Connection successfull!"
            else:
                raise Exception("Could not connect to Keymaster")

            # Pull the configuration
            print "Pulling door configuration..."
            response = connection.send_message(Messages.PULL_CONFIGURATION)
            #print response
            gatekeeper.configure_doors(response)
            if len(gatekeeper.doors) == 0:
                print "No doors to program.  Exiting"
                return
            print "Configured %d doors" % len(gatekeeper.doors)

            # Set the time on each door
            print "Syncing the door clocks..."
            gatekeeper.sync_clocks()

            # Now loop and get new commands
            while True:
                if config['initialSync']:
                    message = Messages.FORCE_SYNC
                    config['initialSync'] = False
                else:
                    message = Messages.PULL_DOOR_CODES
                print "Contacting the Keymaster: %s" % message
                response = connection.send_message(message)
                if len(response) > 2:
                    print "Received new door codes to process"
                    gatekeeper.process_door_codes(response)
                    print "Success!  Sending confirmation."
                    response = connection.send_message(Messages.MARK_SUCCESS)
                    if not response == Messages.SUCCESS_RESPONSE:
                        raise Exception("Did not receive proper success response!")
                else:
                    print "No new door codes"
                print "sleeping %d seconds" % config['POLL_DELAY_SEC']
                time.sleep(config['POLL_DELAY_SEC'])
        except Exception as e:
            traceback.print_exc()
            print "Error: %s" % str(e)
        
if __name__ == "__main__":
    # Load our configuration
    with open('gw_config.json', 'r') as f:
        config = json.load(f)
    config['initialSync'] = "-s" in sys.argv
    
    # Run the app
    app = GatekeeperApp()
    app.run(config)
