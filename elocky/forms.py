from django import forms

from datetime import datetime, timedelta


class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime-local'


class TimeInput(forms.TimeInput):
    input_type = 'time'


class ExepForm(forms.Form):
    date_min = forms.DateTimeField(initial=datetime.now().isoformat(timespec='seconds'), widget=DateTimeInput,
                                   input_formats=['%Y-%m-%dT%H:%M:%S'])
    date_max = forms.DateTimeField(initial=(datetime.now() + timedelta(days=1)).isoformat(timespec='seconds'),
                                   widget=DateTimeInput, input_formats=['%Y-%m-%dT%H:%M:%S'])


class RecuForm(forms.Form):
    time_min = forms.TimeField(widget=TimeInput)
    time_max = forms.TimeField(widget=TimeInput)
    day = forms.ChoiceField(choices=[(1, "Lundi"),
                                     (2, "Mardi"),
                                     (3, "Mercredi"),
                                     (4, "Jeudi"),
                                     (5, "Vendredi"),
                                     (6, "Samedi"),
                                     (7, "Dimanche")])
