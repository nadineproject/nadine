#!/usr/bin/env python
import sys
import json
import time
import logging
import traceback

from core import Messages, EncryptedConnection, Gatekeeper
from threads import Heartbeat, EventWatcher

class GatekeeperApp(object):
    def run(self, config):
        try:
            logging.info("Starting up Gatekeeper...")
            gatekeeper = Gatekeeper(config)
            connection = gatekeeper.get_connection()

            # Sync our system clocks
            gatekeeper.set_system_clock()

            # Test the connection encryption
            if gatekeeper.test_keymaster_connection():
                logging.info("Keymaster encrypted connection successfull!")

            # Pull the configuration
            gatekeeper.configure_doors()
            if len(gatekeeper.doors) == 0:
                logging.error("No doors to program.  Exiting")
                return
            logging.info("Configured %d doors" % len(gatekeeper.doors))

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
                hb_conn_err = False
                while True:
                    # Keep our heartbeat alive
                    if not heartbeat or not heartbeat.is_alive():
                        hb_conn_err = False
                        if heartbeat and heartbeat.error:
                            try:
                                # Heartbeat errors can come from a poor connection to the Keymaster
                                # In cases like these we need to keep retrying to send the log up
                                gatekeeper.send_gatekeper_log("Heartbeat: " + str(heartbeat.error))
                            except Exception as e:
                                hb_conn_err = True
                                logging.warning("Unable to report hearbeat error!: %s" % str(e))
                            time.sleep(5)
                        if not hb_conn_err:
                            logging.info("Starting Heartbeat...")
                            poll_delay = config.get('KEYMASTER_POLL_DELAY_SEC', 5)
                            heartbeat = Heartbeat(connection, poll_delay)
                            heartbeat.setDaemon(True)
                            heartbeat.start()

                    # Keep our event watcher alive
                    if not event_watcher or not event_watcher.is_alive():
                        if event_watcher and event_watcher.error:
                            gatekeeper.send_gatekeper_log("EventWatcher: " + str(event_watcher.error))
                            time.sleep(5)

                        logging.info("Starting Event Watcher...")
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
                logging.info(" Keyboard Interupt!")
                logging.info("Shutting down Heartbeat...")
                if heartbeat and heartbeat.is_alive():
                    heartbeat.stop()
                    #heartbeat.join()
                logging.info("Shutting down Event Watcher...")
                if event_watcher and event_watcher.is_alive():
                    event_watcher.stop()
                    #event_watcher.join()

        except Exception as e:
            traceback.print_exc()
            logging.error("Error: %s" % str(e))


if __name__ == "__main__":
    # Pull the config
    with open('gw_config.json', 'r') as f:
        config = json.load(f)

    # Pull the command line args
    config['initialSync'] = "--sync" in sys.argv
    config['syncClocks'] = "--set-time" in sys.argv
    config['clearCodes'] = "--clear-all" in sys.argv
    if "--debug" in sys.argv:
            config['DEBUG'] = True

    # Configure logging
    log_level = logging.DEBUG if config.get('DEBUG', False) else logging.INFO
    logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=log_level)
    logging.getLogger("requests").setLevel(logging.WARNING)

    # Start the application
    app = GatekeeperApp()
    app.run(config)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
