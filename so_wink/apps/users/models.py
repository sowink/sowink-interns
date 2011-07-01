from django.contrib.auth.models import User
from django.db import models

from commons.models import ModelBase


class Profile(ModelBase):
    user = models.OneToOneField(User, primary_key=True, verbose_name=u'User')
    gender = models.IntegerField(null=True, blank=True, db_index=True)
    birthday = models.DateField(null=True, blank=True, db_index=True)
    height = models.IntegerField(null=True, db_index=True, blank=True)
    winkcash = models.IntegerField()
    coins = models.IntegerField()

    def __unicode__(self):
        return 'User Profile - %s' % (self.user.username)
