from django import forms
from jsignature.forms import JSignatureField
class SignatureForm(forms.Form):
	signature = JSignatureField()