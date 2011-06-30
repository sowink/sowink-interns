from django import forms
from diary.models import Comment, Diary


class DiaryForm(forms.ModelForm):
    def __init__(self, creator, data=None, *args, **kwargs):
        self.creator = creator
        # data is immutable POST data so we have to copy before updating
        if data:
            data = data.copy()
            data.update({'creator': creator.pk})
        super(DiaryForm, self).__init__(data=data, *args, **kwargs)
        # make sure data isn't None
        if data and data.get('is_draft'):
            # Cancel min length.
            del self.fields['text'].min_length
    def clean_is_draft(self):
        is_draft = self.cleaned_data['is_draft']
        # Make sure the instance already exists in DB (Has a pk)
        if is_draft and self.instance.pk and not self.instance.is_draft:
            raise forms.ValidationError("Cannot set back to draft.")
        return is_draft
    def save(self, commit=True, *args, **kwargs):
        diary = super(DiaryForm, self).save(*args, commit=False, **kwargs)
        if commit:
            diary.creator = self.creator
            diary.save()
        return diary
    is_draft = forms.BooleanField(required=False,
                                  error_messages={
                                    'invalid': 'Cannot turn a published diary into a draft.',
                                  })

    text = forms.CharField(
            min_length=500, max_length=10000,
            error_messages={'required': 'Please provide some content.',
                            'min_length': 'Your entry is too short (%(show_value)s characters). It should be at least %(limit_value)s characters.',
                            'max_length': 'Your entry is too long (%(show_value)s characters). It should be at most %(limit_value)s characters.'},
            widget=forms.Textarea(attrs={'cols': 60, 'rows': 20})
            )

    class Meta:
        model = Diary
        fields = ('text', 'is_draft', 'is_private')


class CommentForm(forms.ModelForm):
    def __init__(self, diary, creator, data=None, *args, **kwargs):
        self.creator = creator
        self.diary = diary
        if data:
            data = data.copy()
            data.update({'creator': creator.pk})
        super(CommentForm, self).__init__(data=data, *args, **kwargs)
    def save(self, commit=True, *args, **kwargs):
        comment = super(CommentForm, self).save(*args, commit=False, **kwargs)
        if commit:
            comment.creator = self.creator
            comment.diary = self.diary
            comment.save()
        return comment
    text = forms.CharField(
            min_length=10, max_length=2000,
            error_messages={'required': 'Please provide some content.',
                            'min_length': 'Your entry is too short (%(show_value)s characters). It should be at least %(limit_value)s characters.',
                            'max_length': 'Your entry is too long (%(show_value)s characters). It should be at most %(limit_value)s characters.'},
            widget=forms.Textarea(attrs={'cols': 60, 'rows': 20})
            )
    class Meta:
       model = Comment
       fields = ('text',)
       widgets = {
            'text': forms.Textarea(attrs={'cols': 50, 'rows': 5})
       }
