import sys
import time
import threading

from core import Messages, Door

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
                response = self.connection.send_message(Messages.CHECK_DOOR_CODES)
                if response == Messages.NEW_DATA:
                    print("Heartbeat: There is new data to be processed")
                    self.new_data = True
                else:
                    print("Heartbeat: No new door codes")
            

    def all_clear(self):
        response = self.connection.send_message(Messages.MARK_SUCCESS)
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
            if not self.new_data:
                print("EventWatcher: Polling the doors for events...")
                event_logs = self.gatekeeper.pull_event_logs(1)
                for door_name, logs in event_logs.items():
                    if logs and len(logs) == 1 and 'timestamp' in logs[0]:
                        door = self.gatekeeper.get_door(door_name)
                        #print "EventWatcher: %s ?= %s" % (logs[0]['timestamp'], door.last_event_ts)
                        if logs[0]['timestamp'] != door.last_event_ts:
                            self.new_data = True
                            break
                if not self.new_data:
                    print("EventWatcher: No new event logs")
                
            
            time.sleep(self.poll_delay_sec)

    def all_clear(self):
        print("EventWatcher: all clear")
        self.new_data = False

    def stop(self):
        print("EventWatcher: stop")
        self.poll_delay_sec = 0.1
        self.running = False