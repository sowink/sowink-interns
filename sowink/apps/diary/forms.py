from django import forms

from tower import ugettext_lazy as _lazy

from diary.models import Comment, Diary

ENTRY_REQUIRED = _lazy(u'Please provide some content.')
ENTRY_SHORT = _lazy(u'Your entry is too short (%(show_value)s characters).'
                    'It should be at least %(limit_value)s characters.')
ENTRY_LONG = _lazy(u'Your entry is too long (%(show_value)s characters).'
                   ' It should be at most %(limit_value)s characters.')
SET_DRAFT = _lazy(u'Cannot set a published Diary to a draft.')


class DiaryForm(forms.ModelForm):
    """A diary entry form that requires 500 characters if not a draft."""
    is_draft = forms.BooleanField(required=False,
                                  error_messages={'invalid': SET_DRAFT})

    text = forms.CharField(
            min_length=500, max_length=10000,
            error_messages={'required': ENTRY_REQUIRED,
                            'min_length': ENTRY_SHORT,
                            'max_length': ENTRY_LONG},
            widget=forms.Textarea(attrs={'cols': 60, 'rows': 20}))

    class Meta:
        model = Diary
        fields = ('text', 'is_draft', 'is_private')

    def __init__(self, creator, data=None, *args, **kwargs):
        self.creator = creator
        # data is immutable POST data so we have to copy before updating
        if data:
            data = data.copy()
            data.update({'creator': creator.pk})
        super(DiaryForm, self).__init__(data=data, *args, **kwargs)
        if data and data.get('is_draft'):
            # Cancel min length.
            del self.fields['text'].min_length

    def clean_is_draft(self):
        """"Ensure existing published entry cannot be made a draft."""
        is_draft = self.cleaned_data['is_draft']
        if is_draft and self.instance.pk and not self.instance.is_draft:
            raise forms.ValidationError(SET_DRAFT)
        return is_draft

    def save(self, commit=True, *args, **kwargs):
        diary = super(DiaryForm, self).save(*args, commit=False, **kwargs)
        if commit:
            diary.creator = self.creator
            diary.save()
        return diary


class CommentForm(forms.ModelForm):

    text = forms.CharField(
            required=True, min_length=10, max_length=2000,
            error_messages={'required': ENTRY_REQUIRED,
                            'min_length': ENTRY_SHORT,
                            'max_length': ENTRY_LONG},
            widget=forms.Textarea(attrs={'cols': 60, 'rows': 20}))

    class Meta:
        model = Comment
        fields = ['text']
        widgets = {'text': forms.Textarea(attrs={'cols': 50, 'rows': 5})}

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
