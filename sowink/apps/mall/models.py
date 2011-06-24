from django.db import models

from django.contrib.auth.models import User


class Gift(models.Model):
    '''
    Gift model used to store gifts users can send to other
    users.
    '''
    title = models.CharField(max_length=255)
    creator = models.ForeignKey(User)
    winkcash = models.PositiveIntegerField()
    coins = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True, blank=True)

    def __unicode__(self):
        return self.title


class UserGift(models.Model):
    '''
    UserGift model is used to determine which users have
    sent messages and which users have received messages.
    '''
    gift = models.ForeignKey(Gift, related_name='given')
    creator = models.ForeignKey(User, verbose_name='Sender',
                                related_name='gifts_sent')
    recepient = models.ForeignKey(User, verbose_name='Receiver',
                                  related_name='gifts_received')
    created = models.DateTimeField(auto_now_add=True, blank=True)
    bought_with = models.SmallIntegerField()

    def __unicode__(self):
        return self.recepient.username
