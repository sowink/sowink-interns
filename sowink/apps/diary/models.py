from django.db import models
from django.forms import ModelForm, Textarea
from django.contrib.auth.models import User


class Diary(models.Model):
    author = models.ForeignKey(User, related_name='diaries')
    creation_date = models.DateTimeField('date published')
    title = models.CharField(max_length=140)
    text = models.CharField(max_length=2000)
    is_draft = models.BooleanField(default=False)


class Comment(models.Model):
    diary_entry = models.ForeignKey(Diary, related_name='comments')
    text = models.CharField(max_length=140)
    commenter = models.ForeignKey(User, related_name='posted_comments')
    pub_date = models.DateTimeField('date posted')
 

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
