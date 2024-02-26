from django import forms

from .models import SavedMap
from .validator import (
    hex64,
    validate_metro_map,
    validate_metro_map_v2,
)

import hashlib
import json
import random


RATING_CHOICES = (
    ('likes', 'likes'),
    ('dislikes', 'dislikes'),
)

class CreateMapForm(forms.Form):
    mapdata = forms.JSONField()

    def clean_mapdata(self):
        mapdata = self.cleaned_data['mapdata']

        data_version = mapdata.get('global', {}).get('data_version', 1)
        if data_version == 2:
            mapdata = validate_metro_map_v2(mapdata)
            mapdata['global']['data_version'] = 2
        else:
            try:
                mapdata = validate_metro_map(mapdata)
                mapdata['global']['data_version'] = 1
            except AssertionError as exc:
                raise forms.ValidationError(exc)

        return mapdata

    def clean(self):
        data = self.cleaned_data
        data['urlhash'] = hex64(hashlib.sha256(str(data['mapdata']).encode('utf-8')).hexdigest()[:12])
        data['naming_token'] = hashlib.sha256('{0}'.format(random.randint(1, 100000)).encode('utf-8')).hexdigest()
        data['data_version'] = data['mapdata']['global']['data_version'] # convenience
        return data

class RateForm(forms.Form):

    choice = forms.ChoiceField(widget=forms.HiddenInput, choices=RATING_CHOICES)
    urlhash = forms.CharField(widget=forms.HiddenInput)
