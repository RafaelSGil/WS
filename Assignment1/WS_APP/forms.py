# forms.py
from django import forms

class MovieForm(forms.Form):
    movie_name = forms.CharField(label='Movie Name', max_length=100)

class CastForm(forms.Form):
    cast_name = forms.CharField(label='Actor Name')

class BetweenDatesForm(forms.Form):
    date1 = forms.IntegerField(label='From year')
    date2 = forms.IntegerField(label='To year')

    def clean(self):
        cleaned_data = super().clean()
        date1 = cleaned_data.get('date1')
        date2 = cleaned_data.get('date2')

        if date1 is not None and date2 is not None:
            if date1 >= date2:
                self.add_error('date1', "Date 1 must be lower than Date 2")
                self.add_error('date2', "Date 2 must be higher than Date 1")

        return cleaned_data

class DateForm(forms.Form):
    date = forms.IntegerField(label="Year")

class GenresForm(forms.Form):
    genres = forms.CharField(label="Genres (1+ separated by comma)")

class DirectorForm(forms.Form):
    director = forms.CharField(label="Director Name")


class CombinedSearchForm(forms.Form):
    search_type = forms.ChoiceField(choices=[
        ('title', 'Movie Title'),
        ('actor', 'Actor'),
        ('genre', 'Genre'),
        ('director', 'Director')
    ], label="Search Type")
    search_query = forms.CharField(label='Search Query', max_length=100)

class SearchForm(forms.Form):
    search_query = forms.CharField(label='Search', max_length=100)