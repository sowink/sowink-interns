from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from sowink.models import ModelBase

CURRENCIES = (
    (1, 'WinkCash'),
    (2, 'Coins'),
)


class Gift(ModelBase):
    """Gift model used to store gifts users can send to other users."""

    title = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to=settings.GIFT_IMAGE_PATH, blank=True)
    creator = models.ForeignKey(User)
    winkcash = models.PositiveIntegerField()
    coins = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True, blank=True)

    def __unicode__(self):
        return self.title


class UserGift(ModelBase):
    """UserGift model used to determine who has sent and received a gift."""

    gift = models.ForeignKey(Gift, related_name='given')
    creator = models.ForeignKey(User, verbose_name='Sender',
                                related_name='gifts_sent')
    recipient = models.ForeignKey(User, related_name='gifts_received')
    created = models.DateTimeField(auto_now_add=True, blank=True)
    bought_with = models.SmallIntegerField(choices=CURRENCIES)

    def __unicode__(self):
        return '%s to %s' % (self.creator.username, self.recipient.username)
