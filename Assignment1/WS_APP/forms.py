# forms.py
from django import forms

class MovieForm(forms.Form):
    movie_name = forms.CharField(label='Movie Name', max_length=100)
