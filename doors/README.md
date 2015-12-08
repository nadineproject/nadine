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

Set up the django instance just like you would the main application.  But all you really need to do is
run the managment command 'launch_gatekeeper'. 

Requires flask and cryptography

### Adding a new Gatekeer

The first time a Gatekeeper contacts the Keymaster the IP address of the Gatekeeper is stored in the Keymaster and disabled.  To enable this Gatekeeper, you need to save the shared secret key in the Keymaster database and mark the Gatekeeper enabled.

####TODO: 
 * Magic Key
 * Event Proxy / Logging
 * New Code Mode
 * Find & fill in missing logs
 * Scheduled Lock & Unlock (maybe)
