from django import forms
from django.forms import ModelForm, Textarea
from diary.models import Comment, Diary


class DiaryForm(ModelForm):
    def clean_text(self):
        data = self.cleaned_data['text']
        if len(data) < 500:
            raise forms.ValidationError("Please type 500 characters or more.") 
        #raise forms.ValidationError("error")
        #if "fred@example.com" not in data:
        #    raise forms.ValidationError("You have forgotten about Fred!")

        # Always return the cleaned data, whether you have changed it or
        # not.
        return data

    class Meta:
        model = Diary
        fields = ('text', 'is_draft', 'is_private', )
        widgets = {
            'title': Textarea(attrs={'cols': 80, 'rows': 1}),
            'text': Textarea(attrs={'cols': 80, 'rows': 20}),
        }
        #text = forms.TextField(
        #    min_length=200,
        #    widget=forms.TextInput(attrs={'cols': 80, 'rows': 10})
        #)
        # error_messages = {'invalid': "Please keep the title under 140 characters"}

class CommentForm(ModelForm):
    class Meta:
       model = Comment
       fields = ('text', )
       widgets = {
            'text': Textarea(attrs={'cols': 40, 'rows': 5})
       }
