from django import forms

from .models import SavedMap, IdentifyMap, MAP_TYPE_CHOICES
from .validator import (
    hex64,
    validate_metro_map,
    validate_metro_map_v2,
    validate_metro_map_v3,
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
        if data_version == 3:
            mapdata = validate_metro_map_v3(mapdata)
            mapdata['global']['data_version'] = 3
        elif data_version == 2:
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
        if data.get('mapdata'):
            data['urlhash'] = hex64(hashlib.sha256(str(data['mapdata']).encode('utf-8')).hexdigest()[:12])
            data['naming_token'] = hashlib.sha256('{0}'.format(random.randint(1, 100000)).encode('utf-8')).hexdigest()
            data['data_version'] = data['mapdata']['global']['data_version'] # convenience
        return data

class RateForm(forms.Form):

    choice = forms.ChoiceField(widget=forms.HiddenInput, choices=RATING_CHOICES)
    urlhash = forms.CharField(widget=forms.HiddenInput)

    def clean(self):
        data = self.cleaned_data
        data['g-recaptcha-response'] = self.data.get('g-recaptcha-response')
        return data

class IdentifyForm(forms.ModelForm):

    urlhash = forms.CharField(widget=forms.HiddenInput)
    map_type = forms.ChoiceField(choices=(('', '--------'), *MAP_TYPE_CHOICES), required=False)

    def clean_name(self):
        name = self.cleaned_data['name'] or ''
        return name.strip()

    def clean_map_type(self):
        map_type = self.cleaned_data['map_type'] or ''
        return map_type.strip()

    def clean(self):
        data = self.cleaned_data
        data['g-recaptcha-response'] = self.data.get('g-recaptcha-response')
        return data

    class Meta:
        model = IdentifyMap
        fields = [
            'urlhash',
            'name',
            'map_type',
        ]

class CustomListForm(forms.Form):
    maps = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'rows': 10,
                'class': 'w-100',
                'placeholder': '''225,007
215094
wxtIWRy8
metromapmaker.com/map/XI9PhazG
''',
            },
        ),

    )

    def clean_maps(self):
        maps = self.cleaned_data['maps'] or ''
        maps = maps.strip()
        maps = maps.replace(',', '').replace('#', '')
        return maps
