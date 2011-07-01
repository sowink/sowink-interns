from django.forms import ModelForm, Textarea
from diary.models import Comment, Diary


class DiaryForm(ModelForm):
    class Meta:
        model = Diary
        fields = ('title', 'text', 'is_draft', )
        widgets = {
            'title': Textarea(attrs={'cols': 80, 'rows': 1}),
            'text': Textarea(attrs={'cols': 80, 'rows': 20}),
        }


class CommentForm(ModelForm):
    class Meta:
       model = Comment
       fields = ('text', )
       widgets = {
            'text': Textarea(attrs={'cols': 40, 'rows': 5})
       }
