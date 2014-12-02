import os, uuid

from jsignature.forms import JSignatureField
from jsignature.utils import draw_signature

from django import forms
from django.conf import settings

class SignatureForm(forms.Form):
	signature = JSignatureField()
	
	def has_signature(self):
		return self.is_valid() and self.cleaned_data.get('signature')

	def save_signature(self):
		signature_picture = draw_signature(self.cleaned_data.get('signature'))
		signature_file = "%s.png" % uuid.uuid4()
		signature_path = os.path.join(settings.MEDIA_ROOT, "signatures/%s" % signature_file)
		signature_picture.save(signature_path)
		return signature_file
