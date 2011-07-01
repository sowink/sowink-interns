import datetime

from django.db import models
from django.contrib.auth.models import User


class Diary(models.Model):
    creator = models.ForeignKey(User, related_name='diaries')
    created = models.DateTimeField('date created',
                                   default=datetime.datetime.now())
    created_day = models.DateField(default=datetime.date.today())
    text = models.TextField(max_length=10000)
    is_draft = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)


class Meta(object):
    unique_together = ('creator', 'created_day')


class Comment(models.Model):
    diary = models.ForeignKey(Diary, related_name='comments')
    text = models.TextField(max_length=1000)
    creator = models.ForeignKey(User, related_name='posted_comments')
    created = models.DateTimeField('date posted',
                                   default=datetime.datetime.now())
