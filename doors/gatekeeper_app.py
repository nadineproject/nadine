#!/usr/bin/env python
import sys
import json
import time
import traceback

from core import Messages, EncryptedConnection, Gatekeeper
from threads import Heartbeat, EventWatcher

class GatekeeperApp(object):
    def run(self, config):
        try:
            print "Starting up Gatekeeper..."
            gatekeeper = Gatekeeper(config)
            connection = gatekeeper.get_connection()
            
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
            if config['syncClocks']:
                gatekeeper.sync_clocks()
            
            # Clear out all the door codes if requested
            if config['clearCodes']:
                gatekeeper.clear_all_codes()
                initialSync = True
            
            # Pull new data if requested
            if config['initialSync']:
                gatekeeper.pull_door_codes()
            
            try:
                # Start with a clean bowl
                sys.stdout.flush()
                
                heartbeat = None
                event_watcher = None
                while True:
                    # Keep our heartbeat alive
                    if not heartbeat or not heartbeat.is_alive():
                        if heartbeat and heartbeat.error:
                            gatekeeper.send_gatekeper_log("Heartbeat: " + str(heartbeat.error))
                            time.sleep(5000)
                        
                        print "Starting Heartbeat..."
                        poll_delay = config.get('KEYMASTER_POLL_DELAY_SEC', 5)
                        heartbeat = Heartbeat(connection, poll_delay)
                        heartbeat.setDaemon(True)
                        heartbeat.start()
                    
                    # Keep our event watcher alive
                    if not event_watcher or not event_watcher.is_alive():
                        if event_watcher and event_watcher.error:
                            gatekeeper.send_gatekeper_log("EventWatcher: " + str(event_watcher.error))
                            time.sleep(5000)
                        
                        print "Starting Event Watcher..."
                        poll_delay = config.get('EVENT_POLL_DELAY_SEC', 10)
                        event_watcher = EventWatcher(gatekeeper, poll_delay)
                        event_watcher.setDaemon(True)
                        event_watcher.start()
                    
                    if heartbeat.new_data:
                        gatekeeper.pull_door_codes()
                        heartbeat.all_clear()
                    
                    if event_watcher.new_data:
                        event_logs = gatekeeper.pull_event_logs()
                        gatekeeper.push_event_logs(event_logs)
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
    config['initialSync'] = "--sync" in sys.argv
    config['syncClocks'] = "--set-time" in sys.argv
    config['clearCodes'] = "--clear-all" in sys.argv

    # Start the application
    app = GatekeeperApp()
    app.run(config)
