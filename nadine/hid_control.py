import ssl, urllib, urllib2, base64
from xml.etree import ElementTree

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

HID_DOOR_IP = "172.16.5.20"
HID_DOOR_USER = "admin"
HID_DOOR_PASS = "kickstart"

UNLOCK_COMMAND = 'unlockDoor'
LOCK_COMMAND = 'lockDoor'

###############################################################################################################
# Door Functions
###############################################################################################################

def unlockDoor():
	xml = door_command_xml(UNLOCK_COMMAND)
	return send_xml(xml, HID_DOOR_IP, HID_DOOR_USER, HID_DOOR_PASS)

def lockDoor():
	xml = door_command_xml(LOCK_COMMAND)
	return send_xml(xml, HID_DOOR_IP, HID_DOOR_USER, HID_DOOR_PASS)

###############################################################################################################
# Communication Logic
###############################################################################################################

class DoorController:
    
    def __init__(self):
        consumer_key = getattr(settings, 'HID_DOOR_IP', None)
        if consumer_key is None:
            raise ImproperlyConfigured(XERO_ERROR_MESSAGES['no_key'])

        private_key = getattr(settings, 'XERO_PRIVATE_KEY', None)
        if private_key is None:
            raise ImproperlyConfigured(XERO_ERROR_MESSAGES['no_secret'])

def send_xml(xml, door_ip, username, password):
	door_url = "https://%s/cgi-bin/vertx_xml.cgi" % door_ip
	xml_str = ElementTree.tostring(xml, encoding='utf8', method='xml')
	xml_data = urllib.urlencode({'XML': xml_str})
	request = urllib2.Request(door_url, xml_data)
	base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
	request.add_header("Authorization", "Basic %s" % base64string) 
	context = ssl._create_unverified_context()  
	result = urllib2.urlopen(request, context=context)
	return_code = result.getcode()
	return_xml = result.read()
	result.close()
	return (return_code, return_xml)

###############################################################################################################
# XML Functions
###############################################################################################################

def root_elm():
	return ElementTree.Element('VertXMessage')

def list_doors_xml():
	# <hid:Doors action="LR" responseFormat="status" />
	root = root_elm()
	door_element = ElementTree.SubElement(root, 'hid:Doors')
	door_element.set('action', 'LR')
	door_element.set('responseFormat', 'status')
	return root

def list_credentials_xml(recordOffset, recordCount):
	# <hid:Credentials action="LR" responseFormat="expanded" recordOffset="0" recordCount="10"/>
	root = root_elm()
	elm = ElementTree.SubElement(root, 'hid:Credentials')
	elm.set('action', 'LR')
	elm.set('responseFormat', 'expanded')
	elm.set('recordOffset', str(recordOffset))
	elm.set('recordCount', str(recordCount))
	return root

def door_command_xml(command):
	# <hid:Doors action="CM" command="unlockDoor"/>
	root = root_elm()
	door_element = ElementTree.SubElement(root, 'hid:Doors')
	door_element.set('action', 'CM')
	door_element.set('command', command)
	return root