import sys
import time
import threading

from core import Messages

class Heartbeat(threading.Thread):

    def __init__(self, connection, poll_delay_sec):
        threading.Thread.__init__(self)
        self.connection = connection
        self.poll_delay_sec = poll_delay_sec
        self.new_data = False

    def run(self):
        self.running = True
        print("Heartbeat: polling every %d seconds" % self.poll_delay_sec)

        while self.running:
            time.sleep(self.poll_delay_sec)

            if not self.new_data:
                print("Heartbeat: Contacting the Keymaster...")
                response = self.connection.send_message(Messages.CHECK_IN)
                if response == Messages.NEW_DATA:
                    print("Heartbeat: There is new data to be processed")
                    self.new_data = True
                else:
                    print("Heartbeat: No new door codes")
                
                # Mark this connection successfull
                response = self.connection.send_message(Messages.MARK_SUCCESS)
                if not response == Messages.SUCCESS_RESPONSE:
                    raise Exception("Heartbeat: Did not receive proper success response!")
            

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

    def run(self):
        self.running = True
        print("EventWatcher: Polling every %d seconds" % self.poll_delay_sec)

        while self.running:
            time.sleep(self.poll_delay_sec)
            
            if not self.new_data:
                print("EventWatcher: Polling the doors for events...")
                event_logs = self.gatekeeper.pull_event_logs(1)
                for door_name, logs in event_logs.items():
                    if logs and len(logs) == 1 and 'timestamp' in logs[0]:
                        door = self.gatekeeper.get_door(door_name)
                        last_event_ts = door.get("last_event_ts")
                        #print "EventWatcher: %s ?= %s" % (logs[0]['timestamp'], last_event_ts)
                        if logs[0]['timestamp'] != last_event_ts:
                            # If this is one of our magic keys, do some magic!
                            cardNumber = logs[0].get('cardNumber', None)
                            #print "EventWatcher: Magic key test (%s)" % (cardNumber)
                            self.gatekeeper.magic_key_test(door_name, cardNumber)
                            
                            self.new_data = True
                            break
                if not self.new_data:
                    print("EventWatcher: No new event logs")
    
    def all_clear(self):
        print("EventWatcher: all clear")
        self.new_data = False

    def stop(self):
        print("EventWatcher: stop")
        self.poll_delay_sec = 0.1
        self.running = False