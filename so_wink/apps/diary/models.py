from django.db import models
from django.contrib.auth.models import User


class Diary(models.Model):
    creator = models.ForeignKey(User, related_name='diaries')
    created = models.DateTimeField('date published')
    title = models.CharField(max_length=140)
    text = models.TextField(max_length=50000)
    is_draft = models.BooleanField(default=False)


class Comment(models.Model):
    diary = models.ForeignKey(Diary, related_name='comments')
    text = models.TextField(max_length=5000)
    creator = models.ForeignKey(User, related_name='posted_comments')
    created = models.DateTimeField('date posted')
