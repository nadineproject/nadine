import os
import uuid
import base64
from io import StringIO

from jsignature.forms import JSignatureField
from jsignature.utils import draw_signature

from django import forms
from django.conf import settings


class SignatureForm(forms.Form):
    signature = JSignatureField()
    file_name = None

    def has_signature(self):
        return self.is_valid() and self.cleaned_data.get('signature')

    def signature_file(self):
        if not self.file_name:
            self.file_name = "%s.png" % uuid.uuid4()
        return self.file_name

    def signature_path(self):
        return os.path.join(settings.MEDIA_ROOT, "signatures/%s" % self.signature_file())

    def raw_signature_data(self):
        signature_picture = draw_signature(self.cleaned_data.get('signature'))
        output = StringIO.StringIO()
        signature_picture.save(output, format="PNG")
        contents = output.getvalue()
        output.close()
        image_data = base64.b64encode(contents)
        return image_data

    def save_signature(self):
        signature_picture = draw_signature(self.cleaned_data.get('signature'))
        signature_picture.save(self.signature_path())
        return self.signature_file()


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
