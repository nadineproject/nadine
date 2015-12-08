# HID Keymaster/Gatekeeper Door System

## Keymaster

The Keymaster runs on the main django application server along side the main application. 

## Gatekeeper

The Gatekeeper runs on a remote system close to the door locks.  This system should be locked down to only allow communication between it and the keymaster.

### Gatekeeper Functions
Gatekeeper runs two processes: one to poll the keymaster for changes to make (such as adding or removing keys), and another to relay realtime events to the keymaster as they happen on the doors.

#### Event Proxy
 * Accept event notifications from doors, convert to JSON, add Door ID, and send along to the Keymaster to be logged
 * Interpret response from Keymaster in the case the "Magic Key" has been scanned (and toggle lock state of all doors)
 
#### Heartbeat (Gatekeeper App)
 * Upon booting, secure handsake with the Keymaster and pull door configuration for Keymaster
 * Poll Keymaster for instructions periodically (every minute) and process the following instructions:
   * Refresh access permissions on the doors with data provided
   * Collect and deliver past logs to Keymaster from a certain timestamp (to fill in missing entries)

### Gatekeeper Setup

* Generate an encrytion key:
`./manage.py generate_key`

* Create your config file (gw_config.json):

````
{
   "ENCRYPTION_KEY": "THE_KEY_YOU_GENERATED",
   "KEYMASTER_URL": "http://127.0.0.1:8000/doors/keymaster/",
   "POLL_DELAY_SEC": 60
}
````

* Install neccessary libraries:
`pip install flask cryptography requests`

* Run the app:
`./gateway_app.py`

### Adding a new Gatekeer

The first time a Gatekeeper contacts the Keymaster the IP address of the Gatekeeper is stored in the Keymaster and disabled.  To enable, you need to save the shared secret key in the Keymaster database and mark the Gatekeeper enabled.

####TODO: 
 * Magic Key (toggle lock/unlock)
 * Event Proxy / Logging
 * New Code Mode
 * Find & fill in missing logs
 * Scheduled Lock & Unlock (maybe)
