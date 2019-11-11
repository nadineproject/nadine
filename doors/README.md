# HID Keymaster/Gatekeeper Door System

## Keymaster

The Keymaster runs on the main Django application server along side the main application.

## Gatekeeper (coor.py)

The Gatekeeper runs on a remote system close to the door locks.  This system should be locked down to only allow communication between it and the keymaster.

The gatekeeper runs two processes: one to poll the Keymaster for changes to make (such as adding or removing keys), and another to relay door events (access granted/denied, door unlocked, etc) to the Keymaster.

#### Heartbeat (threads.py)
 * Upon booting, secure handsake with the Keymaster to verify connection
 * Pull door configuration and last door event timestamp for each door
 * Poll Keymaster for new codes periodically (KEYMASTER_POLL_DELAY_SEC)
 * Alert Gatekeeper to perform a full sync for each door when new codes are found.

#### Event Watcher (threads.py)
 * Poll each door for latest event timestamp (EVENT_POLL_DELAY_SEC)
 * Alert Gatekeeper to upload latest batch of events (EVENT_SYNC_COUNT) to Keymaster

#### Event Proxy (INACTIVE)
There is a bug in the HID controllers that doesn't allow for this feature to work.

 * Accept event notifications from doors in real time
 * Convert to JSON, add Door ID, and send along to the Keymaster to be logged
 * Interpret response from Keymaster in the case the "Magic Key" has been scanned (and toggle lock state of all doors)


### Gatekeeper Setup

* Generate a Keymaster encrytion key:
`./manage.py generate_key`

* Create your config file (nadine/doors/gw_config.json):

````
{
   "KEYMASTER_SECRET": "THE_KEY_YOU_GENERATED",
   "KEYMASTER_URL": "http://127.0.0.1:8000/doors/keymaster/",
   "KEYMASTER_POLL_DELAY_SEC": 5,
   "EVENT_POLL_DELAY_SEC": 20,
   "EVENT_SYNC_COUNT": 100,
}
````

* Add optional config attributes
  * CARD_SECRET = If set this private key is used to encode door keys before sending them off to the keymaster
  * LOCK_KEY = A key code that will send a lock command to a given door
  * UNLOCK_KEY = A key code that will send a unlock command to a given door

* Install necessary libraries:
`pipenv install`

* Run the app:
`pipenv run ./gatekeeper_app.py`

### Adding a new Gatekeer

The first time a Gatekeeper contacts the Keymaster the IP address of the Gatekeeper is stored in the Keymaster and disabled.  To enable, you need to save the shared secret key in the Keymaster database and mark the Gatekeeper enabled.
