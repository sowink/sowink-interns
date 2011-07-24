import datetime
from django.db import models
from django.forms import ModelForm
from django.contrib.auth.models import User

class ProfileVisit(models.Model):
    # ForeignKey('Profile') --> ForeignKey(User)
    visited_user = models.ForeignKey(User, related_name='visits_received')
    visitor = models.ForeignKey(User, related_name='visits_sent')
    mojo = models.PositiveIntegerField(verbose_name='Interpersonal Mojo',
                                       default=10)
    created = models.DateTimeField(default=datetime.datetime.now)

class Admire(models.Model):
    admirer = models.ForeignKey(User, related_name='admirer')
    being_admired = models.ForeignKey(User, related_name='admire_starter')
    times_tried = models.PositiveIntegerField(verbose_name='Times Tried to Guess the Admirer')
    
    # see: https://docs.djangoproject.com/en/dev/ref/models/fields/#datefield
    modified = models.DateTimeField(auto_now=True)

    # created = models.DateTimeField(default=datetime.datetime.now)
    created = models.DateTimeField(auto_now_add=True) 
