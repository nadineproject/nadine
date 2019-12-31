import sys
import time
import logging
import threading

from core import Messages

class Heartbeat(threading.Thread):

    def __init__(self, connection, poll_delay_sec):
        threading.Thread.__init__(self)
        self.connection = connection
        self.poll_delay_sec = poll_delay_sec
        self.new_data = False
        self.error = None
        self.debug = False

    def run(self):
        self.running = True
        logging.info("Heartbeat: polling every %d seconds" % self.poll_delay_sec)

        try:
            while self.running:
                time.sleep(self.poll_delay_sec)

                if not self.new_data:
                    logging.debug("Heartbeat: Contacting the Keymaster...")
                    response = self.connection.send_message(Messages.CHECK_IN)
                    if response == Messages.NEW_DATA:
                        logging.info("Heartbeat: There is new data to be processed")
                        self.new_data = True
                    else:
                        logging.debug("Heartbeat: No new door codes")

                    # Mark this connection successfull
                    response = self.connection.send_message(Messages.MARK_SUCCESS)
                    if not response == Messages.SUCCESS_RESPONSE:
                        raise Exception("Heartbeat: Did not receive proper success response!")
        except Exception as e:
            logging.error("Heartbeat Exception: %s" % e)
            self.error = e

    def all_clear(self):
        response = self.connection.send_message(Messages.MARK_SYNC)
        if not response == Messages.SUCCESS_RESPONSE:
            raise Exception("Heartbeat: Did not receive proper success response!")
        self.new_data = False

    def stop(self):
        self.poll_delay_sec = 0.1
        self.running = False


class EventWatcher(threading.Thread):

    def __init__(self, gatekeeper, poll_delay_sec):
        threading.Thread.__init__(self)
        self.gatekeeper = gatekeeper
        self.poll_delay_sec = poll_delay_sec
        self.new_data = False
        self.error = None

    def run(self):
        self.running = True
        logging.info("EventWatcher: Polling every %d seconds" % self.poll_delay_sec)

        try:
            while self.running:
                time.sleep(self.poll_delay_sec)

                if not self.new_data:
                    logging.debug("EventWatcher: Polling the doors for events...")
                    event_logs = self.gatekeeper.pull_event_logs(1)
                    for door_name, logs in list(event_logs.items()):
                        if logs and len(logs) == 1 and 'timestamp' in logs[0]:
                            door = self.gatekeeper.get_door(door_name)
                            last_event_ts = door.get("last_event_ts")
                            if logs[0]['timestamp'] != last_event_ts:
                                # If this is one of our magic keys, do some magic!
                                cardNumber = logs[0].get('cardNumber', None)
                                self.gatekeeper.magic_key_test(door_name, cardNumber)

                                self.new_data = True
                                break
                    if not self.new_data:
                        logging.debug("EventWatcher: No new event logs")
        except Exception as e:
            logging.error("EventWatcher Exception: %s" % e)
            self.error = e

    def all_clear(self):
        logging.info("EventWatcher: all clear")
        self.new_data = False

    def stop(self):
        logging.info("EventWatcher: stop")
        self.poll_delay_sec = 0.1
        self.running = False


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
