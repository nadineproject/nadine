import logging
import ssl, urllib, urllib2, base64
from xml.etree import ElementTree

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

###############################################################################################################
# Communication Logic
###############################################################################################################

class DoorController:
    
    def __init__(self, ip_address, username, password):
        self.door_ip = ip_address
        self.door_user = username
        self.door_pass = password

    def send_xml_str(self, xml_str):
        logger.debug("Sending: %s" % xml_str)
        door_url = "https://%s/cgi-bin/vertx_xml.cgi" % self.door_ip
        xml_data = urllib.urlencode({'XML': xml_str})
        request = urllib2.Request(door_url, xml_data)
        base64string = base64.encodestring('%s:%s' % (self.door_user, self.door_pass)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string) 
        context = ssl._create_unverified_context()  
        result = urllib2.urlopen(request, context=context)
        return_code = result.getcode()
        return_xml = result.read()
        result.close()
        logger.debug("Response code: %d" % return_code)
        logger.debug("Response: %s" % return_xml)
        return (return_code, return_xml)

    def send_xml(self, xml):
        xml_str = ElementTree.tostring(xml, encoding='utf8', method='xml')
        return self.send_xml_str(xml_str)
    
    def test_connection(self):
        test_xml = list_doors()
        code, response = self.send_xml(test_xml)
        if code != 200:
            raise Exception("Did not receive 200 return code")
        error = get_error(response)
        if error:
            raise Exception("Received an error: %s" % error)

###############################################################################################################
# Helper Functions
###############################################################################################################

def send_xml(ip_address, username, password, xml_str):
    controller = DoorController(ip_address, username, password)
    return controller.send_xml_str(xml_str)

def add_door_code(user, door_code):
    # Create cardholder
    # Create credential
    # Assign credential
    # Assign schedule
    pass

# def unlockDoor():
#     xml = door_command_xml("unlockDoor")
#     controller = DoorController()
#     return controller.send_xml(xml)
#
# def lockDoor():
#     xml = door_command_xml("lockDoor")
#     controller = DoorController()
#     return controller.send_xml(xml)

def get_error(xml_str):
    if "errorMessage" in xml_str:
        e_start = xml_str.index('errorMessage') + 14
        e_end = xml_str.index('"', e_start)
        return xml_str[e_start:e_end]

###############################################################################################################
# Base XML Functions
###############################################################################################################


def root_elm():
    return ElementTree.Element('VertXMessage')


###############################################################################################################
# Door Commands
###############################################################################################################


def doors_elm(action):
    root = root_elm()
    elm = ElementTree.SubElement(root, 'hid:Doors')
    elm.set('action', action)
    return (root, elm)

# <hid:Doors action="LR" responseFormat="status" />
def list_doors():
    root, elm = doors_elm('LR')
    elm.set('responseFormat', 'status')
    return root

# <hid:Doors action="CM" command="lockDoor"/>
# <hid:Doors action="CM" command="unlockDoor"/>
def door_command(command):
    root, elm = doors_elm('CM')
    elm.set('command', command)
    return root


###############################################################################################################
# Cardholder Commands
###############################################################################################################


# Parent element
def cardholders_parent_elm(action):
    root = root_elm()
    parent = ElementTree.SubElement(root, 'hid:Cardholders')
    parent.set('action', action)
    return (root, parent)

# Child element
def cardholder_child_elm(action):
    root, parent = cardholders_parent_elm(action)
    child = ElementTree.SubElement(parent, "hid:Cardholder")
    return (root, child)

# <hid:Cardholders action="LR" responseFormat="expanded" recordOffset="0" recordCount="10"/>
def list_cardholders(recordOffset, recordCount):
    root, elm = cardholders_parent_elm('LR')
    elm.set('responseFormat', 'expanded')
    elm.set('recordOffset', str(recordOffset))
    elm.set('recordCount', str(recordCount))
    return root

# <hid:Cardholders action="AD">
#     <hid:Cardholder forename="Test"
#                     middleName="M"
#                     surname="Aaaaaa"
#                     exemptFromPassback="true"
#                     extendedAccess="false"
#                     confirmingPin=""
#                     email="test@example.com"
#                     custom1="c1"
#                     custom2="c2"
#                     phone="800-555-1212" />
# </hid:Cardholders>
def create_cardholder(first_name, last_name, email, username):
    root, elm = cardholder_child_elm('AD')
    elm.set('forename', first_name)
    elm.set('surname', last_name)
    elm.set('email', email)
    elm.set('custom1', username)
    return root

# <hid:Cardholders action="DD" cardholderID="647"/>
def delete_cardholder(cardholderID):
    root, elm = cardholders_parent_elm('DD')
    elm.set('cardholderID', cardholderID)
    return root


###############################################################################################################
# Credential Commands
###############################################################################################################


# Parent element
def credentials_parent_elm(action):
    root = root_elm()
    parent = ElementTree.SubElement(root, 'hid:Credentials')
    parent.set('action', action)
    return (root, parent)

# Child element
def credential_child_elm(action):
    root, parent = credentials_parent_elm(action)
    child = ElementTree.SubElement(parent, "hid:Credential")
    return (root, child)

# <hid:Credentials action="LR" responseFormat="expanded" recordOffset="0" recordCount="10"/>
def list_credentials(recordOffset, recordCount):
    root, elm = credentials_parent_elm('LR')
    elm.set('responseFormat', 'expanded')
    elm.set('recordOffset', str(recordOffset))
    elm.set('recordCount', str(recordCount))
    return root

# <hid:Credentials action="AD">
#     <hid:Credential cardNumber="012345AB" isCard="true" endTime="2015-06-28T23:59:59"/>
# </hid:Credentials>
def create_credential(cardNumber):
    root, child = credential_child_elm('AD')
    child.set('isCard', 'true')
    child.set('cardNumber', cardNumber)
    return root

# <hid:Credentials action="UD" rawCardNumber="012345AB" isCard="true">
#     <hid:Credential cardholderID="647"/>
# </hid:Credentials>
def assign_credential():
    pass

# <hid:Credentials action="UD" rawCardNumber="012345AB" isCard="true">
#     <hid:Credential cardholderID="647"/>
# </hid:Credentials>
def remove_credential():
    pass


###############################################################################################################
# RoleSet Commands
###############################################################################################################


def rollset_elm(action):
    root = root_elm()
    elm = ElementTree.SubElement(root, 'hid:RoleSet')
    elm.set('action', action)
    return (root, elm)

# <hid:RoleSet action="UD" roleSetID="1">
#     <hid:Roles>
#         <hid:Role roleID="1" scheduleID="1" resourceID="0"/>
#     </hid:Roles>
# </hid:RoleSet>
def assign_roll():
    pass


###############################################################################################################
# Schedule Commands
###############################################################################################################


def schedule_elm(action):
    root = root_elm()
    elm = ElementTree.SubElement(root, 'hid:Schedules')
    elm.set('action', action)
    return (root, elm)
    
# <hid:Schedules action="LR" recordOffset="0" recordCount="10"/>
def list_schedules(recordOffset, recordCount):
    root, elm = schedule_elm('LR')
    elm.set('recordOffset', str(recordOffset))
    elm.set('recordCount', str(recordCount))
    return root

def assign_schedule():
    pass

def remove_schedule():
    pass