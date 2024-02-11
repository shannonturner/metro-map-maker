from django import forms

RATING_CHOICES = (
    ('likes', 'likes'),
    ('dislikes', 'dislikes'),
)

class RateForm(forms.Form):

    choice = forms.ChoiceField(widget=forms.HiddenInput, choices=RATING_CHOICES)
    urlhash = forms.CharField(widget=forms.HiddenInput)
