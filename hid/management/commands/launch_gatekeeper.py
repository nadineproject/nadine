import time
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from hid.models import Gatekeeper, Door, Messages

class Command(BaseCommand):
    help = "Launch the Gatekeeper"
    args = ""
    requires_system_checks = False

    def handle(self, *labels, **options):
        poll_delay = getattr(settings, 'HID_POLL_DELAY_SEC', 60)

        try:
            print "Starting up Gatekeeper..."
            gatekeeper = Gatekeeper.objects.from_settings()
            connection = gatekeeper.get_encrypted_connection()
                
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

            # Load the data to test the configuration
            print "Loading data from doors..."
            gatekeeper.load_data()

            # Now loop and get new commands
            while True:
                print "Contacting the Keymaster..."
                response = connection.send_message(Messages.PULL_DOOR_CODES)
                if len(response) > 2:
                    print "Received new door codes to process"
                    gatekeeper.process_door_codes(response)
                    print "Success!  Sending confirmation."
                    response = connection.send_message(Messages.MARK_SUCCESS)
                    if not response == Messages.SUCCESS_RESPONSE:
                        raise Exception("Did not receive proper success response!")
                else:
                    print "No new door codes"
                time.sleep(poll_delay)
        except Exception as e:
            traceback.print_exc()
            print "Error: %s" % str(e)
    
