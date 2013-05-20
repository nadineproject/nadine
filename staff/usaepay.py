from suds.client import Client
from suds.xsd.sxbasic import Import
url="https://www.usaepay.com/soap/gate/26FA8F7A/usaepay.wsdl"
imp = Import('http://schemas.xmlsoap.org/soap/encoding/', location='http://schemas.xmlsoap.org/soap/encoding/')
imp.filter.add('http://ws.client.com/Members.asmx')
client = Client(url,plugins=[ImportDoctor(imp)]
