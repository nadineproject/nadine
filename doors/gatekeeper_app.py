#!/usr/bin/env python
import time
import traceback

from core import Messages, EncryptedConnection, Gatekeeper

# HID Door System
# Encryption Key must be a URL-safe base64-encoded 32-byte key.
# https://cryptography.io/en/latest/fernet/
ENCRYPTION_KEY = "tsw8ZGfhS72NyQGBYYUwk1OLYOW45hS4XvUQA07qrDc="
KEYMASTER_URL = "http://127.0.0.1:8000/doors/keymaster/"
POLL_DELAY_SEC = 60
# TODO - Move settings to settings file

class GatekeeperApp(object):
    def run(self):
        # Start with a full sync
        forcesync = True
        
        try:
            print "Starting up Gatekeeper..."
            connection = EncryptedConnection(ENCRYPTION_KEY, KEYMASTER_URL)
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
                if forcesync:
                    message = Messages.FORCE_SYNC
                    forcesync = False
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
                time.sleep(POLL_DELAY_SEC)
        except Exception as e:
            traceback.print_exc()
            print "Error: %s" % str(e)
        
if __name__ == "__main__":
    app = GatekeeperApp()
    app.run()
