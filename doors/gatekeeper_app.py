#!/usr/bin/env python
import sys
import json
import time
import traceback

from core import Messages, EncryptedConnection, Gatekeeper
from threads import Heartbeat, EventWatcher

class GatekeeperApp(object):
    def run(self, config, syncClocks, initialSync, clearCodes):
        try:
            print "Starting up Gatekeeper..."
            connection = EncryptedConnection(config['ENCRYPTION_KEY'], config['KEYMASTER_URL'])
            gatekeeper = Gatekeeper(connection)
            
            # Test the connection
            if gatekeeper.test_keymaster_connection():
                print "Keymaster connection successfull!"
            
            # Pull the configuration
            gatekeeper.configure_doors()
            if len(gatekeeper.doors) == 0:
                print "No doors to program.  Exiting"
                return
            print "Configured %d doors" % len(gatekeeper.doors)
            
            # Set the time on each door
            if syncClocks:
                gatekeeper.sync_clocks()
            
            # Clear out all the door codes if requested
            if clearCodes:
                gatekeeper.clear_all_codes()
                initialSync = True
            
            # Pull new data if requested
            if initialSync:
                gatekeeper.pull_door_codes()
                gatekeeper.push_event_logs()
            
            try:
                heartbeat = None
                event_watcher = None
                while True:
                    # Keep our heartbeat alive
                    if not heartbeat or not heartbeat.is_alive():
                        print "Starting Heartbeat..."
                        poll_delay = config.get('KEYMASTER_POLL_DELAY_SEC', 5)
                        heartbeat = Heartbeat(connection, poll_delay)
                        heartbeat.setDaemon(True)
                        heartbeat.start()
                    
                    # Keep our event watcher alive
                    if not event_watcher or not event_watcher.is_alive():
                        print "Starting Event Watcher..."
                        poll_delay = config.get('EVENT_POLL_DELAY_SEC', 10)
                        event_watcher = EventWatcher(gatekeeper, poll_delay)
                        event_watcher.setDaemon(True)
                        event_watcher.start()
                    
                    if heartbeat.new_data:
                        gatekeeper.pull_door_codes()
                        heartbeat.all_clear()
                    
                    if event_watcher.new_data:
                        cnt = config.get('EVENT_SYNC_COUNT', 100)
                        gatekeeper.push_event_logs(record_count=cnt)
                        event_watcher.all_clear()
                    
                    time.sleep(.1)
            except KeyboardInterrupt:
                print " Keyboard Interupt!"
                print "Shutting down Heartbeat..."
                if heartbeat and heartbeat.is_alive():
                    heartbeat.stop()
                    #heartbeat.join()
                print "Shutting down Event Watcher..."
                if event_watcher and event_watcher.is_alive():
                    event_watcher.stop()
                    #event_watcher.join()
                print "Done!"

        except Exception as e:
            traceback.print_exc()
            print "Error: %s" % str(e)


if __name__ == "__main__":
    # Pull the config
    with open('gw_config.json', 'r') as f:
        config = json.load(f)
    
    # Pull the command line args
    initialSync = "--sync" in sys.argv
    syncClocks = "--set-time" in sys.argv
    clearCodes = "--clear-all" in sys.argv

    # Start the application
    app = GatekeeperApp()
    app.run(config, syncClocks, initialSync, clearCodes)
