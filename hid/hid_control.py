import ssl, urllib, urllib2, base64
from xml.etree import ElementTree

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

#HID_DOOR_IP = "172.16.5.20"
#HID_DOOR_USER = "user"
#HID_DOOR_PASS = "password"

UNLOCK_COMMAND = 'unlockDoor'
LOCK_COMMAND = 'lockDoor'

###############################################################################################################
# Door Functions
###############################################################################################################

def unlockDoor():
    xml = door_command_xml(UNLOCK_COMMAND)
    controller = DoorController()
    return controller.send_xml(xml)

def lockDoor():
    xml = door_command_xml(LOCK_COMMAND)
    controller = DoorController()
    return controller.send_xml(xml)

###############################################################################################################
# Communication Logic
###############################################################################################################

class DoorController:
    
    def __init__(self):
        self.door_ip = getattr(settings, 'HID_DOOR_IP', None)
        if self.door_ip is None:
            raise ImproperlyConfigured("Missing HID_DOOR_IP setting")

        self.door_user = getattr(settings, 'HID_DOOR_USER', None)
        if self.door_user is None:
            raise ImproperlyConfigured("Missing HID_DOOR_USER setting")

        self.door_pass = getattr(settings, 'HID_DOOR_PASS', None)
        if self.door_pas is None:
            raise ImproperlyConfigured("Missing HID_DOOR_PASS setting")

    def send_xml(xml, door_ip, username, password):
        door_url = "https://%s/cgi-bin/vertx_xml.cgi" % self.door_ip
        xml_str = ElementTree.tostring(xml, encoding='utf8', method='xml')
        xml_data = urllib.urlencode({'XML': xml_str})
        request = urllib2.Request(door_url, xml_data)
        base64string = base64.encodestring('%s:%s' % (self.door_user, self.door_pass)).replace('\n', '')
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