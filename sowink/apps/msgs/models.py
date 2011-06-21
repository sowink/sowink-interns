from django.db import models
from django.contrib.auth.models import User


class Message(models.Model):
    to_user = models.ForeignKey(User, related_name='to_user')
    from_user = models.ForeignKey(User, related_name='from_user')
    msg = models.TextField()
    date = models.DateTimeField(auto_now_add=True, blank=True)

    def __unicode__(self):
        return self.to_user
