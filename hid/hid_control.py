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

    def door_url(self):
        door_url = "https://%s/cgi-bin/vertx_xml.cgi" % self.door_ip
        return door_url

    def send_xml_str(self, xml_str):
        logger.debug("Sending: %s" % xml_str)
        
        xml_data = urllib.urlencode({'XML': xml_str})
        request = urllib2.Request(self.door_url(), xml_data)
        base64string = base64.encodestring('%s:%s' % (self.door_user, self.door_pass)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string) 
        context = ssl._create_unverified_context()
        context.set_ciphers('RC4-SHA')
        
        result = urllib2.urlopen(request, context=context)
        return_code = result.getcode()
        return_xml = result.read()
        result.close()
        
        logger.debug("Response code: %d" % return_code)
        logger.debug("Response: %s" % return_xml)
        if return_code != 200:
            raise Exception("Did not receive 200 return code")
        error = get_error(return_xml)
        if error:
            raise Exception("Received an error: %s" % error)
        
        return return_xml

    def send_xml(self, xml):
        xml_str = ElementTree.tostring(xml, encoding='utf8', method='xml')
        return self.send_xml_str(xml_str)
    
    def test_connection(self):
        test_xml = list_doors()
        self.send_xml(test_xml)

    def load_cardholders(self):
        people = {}
        offset = 0
        count = 10
        moreRecords = True
        while moreRecords:
            logger.debug("offset: %d, count: %d" % (offset, count))
            xml_str = self.send_xml(list_cardholders(offset, count))
            xml = ElementTree.fromstring(xml_str)
            for child in xml[0]:
                person = child.attrib
                cardholderID = person['cardholderID']
                person['full_name'] = "%s %s " % (person['forename'], person['surname'])
                if 'custom1' in person:
                    person['username'] = person['custom1']
                people[cardholderID] = person
            returned = int(xml[0].attrib['recordCount'])
            logger.debug("returned: %d cardholders" % returned)
            if count > returned:
                moreRecords = False
            else:
                offset = offset + count
        self.cardholders = people
        logger.debug(self.cardholders)

    def get_cardholders(self):
        if not 'cardholders' in self.__dict__:
            self.load_cardholders()
        return self.cardholders

    def get_cardholder_by_id(self, id):
        chs = self.get_cardholders()
        if id in chs:
            return chs[id]
        return None
    
    def get_cardholder_by_username(self, username):
        for person in self.get_cardholders():
            if 'username' in person and person['username'] == username:
                return person
        return None

    def load_credentials(self):
        # This method pulls all the credentials and infuses the cardholders with their card numbers.
        people = self.get_cardholders()
        offset = 0
        count = 10
        moreRecords = True
        while moreRecords:
            xml_str = self.send_xml(list_credentials(offset, count))
            xml = ElementTree.fromstring(xml_str)
            for child in xml[0]:
                card = child.attrib
                if 'cardholderID' in card:
                    cardholderID = card['cardholderID']
                    cardNumber = card['rawCardNumber']
                    people[cardholderID]['cardNumber'] = cardNumber
            returned = int(xml[0].attrib['recordCount'])
            logger.debug("returned: %d credentials" % returned)
            if count > returned:
                moreRecords = False
            else:
                offset = offset + count

    def pull_events(self, recordCount):
        # First pull the overview to get the current recordmarker and timestamp
        event_xml_str = self.send_xml(list_events())
        event_xml = ElementTree.fromstring(event_xml_str)
        rm = event_xml[0].attrib['currentRecordMarker']
        ts = event_xml[0].attrib['currentTimestamp']
        
        events = []
        event_xml_str = self.send_xml(list_events(recordCount, rm, ts))
        event_xml = ElementTree.fromstring(event_xml_str)
        for child in event_xml[0]:
            event_str = get_event_detail(child.attrib)
            events.append(event_str)
        return events


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

# <hid:Error action="RS" elementType="hid:EventMessages" errorCode="5013" errorReporter="vertx" errorMessage="Error getting event history"/>
# Just using strings on this guy to keep things simple
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
# Event Commands
###############################################################################################################


def event_elm(action):
    root = root_elm()
    elm = ElementTree.SubElement(root, 'hid:EventMessages')
    elm.set('action', action)
    return (root, elm)

# <hid:EventMessages action="DR"/>
def display_recent():
    root, elm = event_elm('DR')
    return root

# <hid:EventMessages action="LR" recordCount="1" historyRecordMarker="2233" historyTimestamp="1428541357"/>
def list_events(recordCount=None, recordMarker=None, timestamp=None):
    root, elm = event_elm('LR')
    if recordCount:
        elm.set('recordCount', str(recordCount))
    if recordMarker:
        elm.set('historyRecordMarker', str(recordMarker))
    if timestamp:
        elm.set('historyTimestamp', str(timestamp))
    return root

event_details = {}
event_details["1022"] = "Denied Access - Card Not Found"
event_details["1023"] = "Denied Access - Access PIN Not Found"
event_details["2020"] = "Granted Access"
event_details["2021"] = "Granted Access -  Extended Time"
event_details["2024"] = "Denied Access - Schedule "
event_details["2029"] = "Denied Access - Wrong PIN"
event_details["2036"] = "Denied Access - Card Expired"
event_details["2042"] = "Denied Access - PIN Lockout"
event_details["2043"] = "Denied Access - Unassigned Card"
event_details["2044"] = "Denied Access - Unassigned Access PIN"
event_details["2046"] = "Denied Access - PIN Expired"
event_details["4034"] = "Alarm Acknowledged"
event_details["4035"] = "Door Locked-Scheduled"
event_details["4036"] = "Door Unlocked-Scheduled"
event_details["4041"] = "Door Forced Alarm"
event_details["4042"] = "Door Held Alarm"
event_details["4043"] = "Tamper Switch Alarm"
event_details["4044"] = "Input A Alarm"
event_details["4045"] = "Input B Alarm"
event_details["7020"] = "Time Set"
event_details["12031"] = "Granted Access - Manual"
event_details["12032"] = "Door Unlocked"
event_details["12033"] = "Door Locked"

def get_event_detail(event_dict):
    type = event_dict['eventType']
    # The two most common events  
    if type == "1022":
        event_text = "Card Not Found (%s) " % event_dict['rawCardNumber']
    elif type == "2020":
        event_text = "Access Granted (%s %s)" % (event_dict['forename'], event_dict['surname'])
    else:
        event_text = event_details[type]
    return "%s: %s" % (event_dict['timestamp'], event_text)

#<?xml version="1.0" encoding="UTF-8"?><VertXMessage xmlns:hid="http://www.hidcorp.com/VertX"><hid:EventMessages action="RL" historyRecordMarker="0" historyTimestamp="947256029" recordCount="16" moreRecords="false" ><hid:EventMessage readerAddress="0" ioState="0" eventType="4034" timestamp="2000-01-20T02:22:57" /><hid:EventMessage readerAddress="0" rawCardNumber="010F2B8E" eventType="1022" timestamp="2000-01-01T00:13:34" /><hid:EventMessage readerAddress="0" cardholderID="1" forename="Jacob" surname="Sayles" eventType="2020" timestamp="2000-01-01T00:13:23" /><hid:EventMessage readerAddress="0" rawCardNumber="009B4C9B" eventType="1022" timestamp="2000-01-01T00:13:11" /><hid:EventMessage readerAddress="0" commandStatus="true" eventType="12031" timestamp="2000-01-01T00:13:02" /><hid:EventMessage readerAddress="0" commandStatus="true" eventType="12033" timestamp="2000-01-01T00:12:58" /><hid:EventMessage readerAddress="0" rawCardNumber="010F2B8E" eventType="1022" timestamp="2000-01-01T00:12:14" /><hid:EventMessage readerAddress="0" rawCardNumber="009B4C9B" eventType="1022" timestamp="2000-01-01T00:12:05" /><hid:EventMessage readerAddress="0" cardholderID="1" forename="Jacob" surname="Sayles" eventType="2020" timestamp="2000-01-01T00:11:57" /><hid:EventMessage readerAddress="0" rawCardNumber="01D609AD" eventType="1022" timestamp="2000-01-01T00:10:33" /><hid:EventMessage readerAddress="0" rawCardNumber="010F2B8E" eventType="1022" timestamp="2000-01-01T00:10:25" /><hid:EventMessage readerAddress="0" rawCardNumber="009B4C9B" eventType="1022" timestamp="2000-01-01T00:10:20" /><hid:EventMessage readerAddress="0" commandStatus="true" eventType="12032" timestamp="2000-01-01T00:10:14" /><hid:EventMessage readerAddress="0" ioState="0" eventType="4034" timestamp="2000-01-01T00:03:14" /><hid:EventMessage readerAddress="0" ioState="0" eventType="4034" timestamp="2000-01-01T00:00:52" /><hid:EventMessage readerAddress="0" ioState="0" eventType="4034" timestamp="2000-01-07T14:40:29" /></hid:EventMessages></VertXMessage>

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