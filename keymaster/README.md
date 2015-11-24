# HID Keymaster/Gatekeeper Door System

## Keymaster

The Keymaster runs on the main django application server along side the main application. 

## Gatekeeper

The Gatekeeper runs on a remote system close to the door locks.  This system should be locked down to only allow communication between it and the keymaster.

### Gatekeeper Setup

Set up the django instance just like you would the main application.  But all you really need to do is
run the managment command 'launch_gatekeeper'. 

### Adding a new Gatekeer

The first time a Gatekeeper contacts the Keymaster the IP address of the Gatekeeper is stored in the Keymaster and disabled.  To enable this Gatekeeper, you need to save the shared secret key in the Keymaster database and mark the Gatekeeper enabled.