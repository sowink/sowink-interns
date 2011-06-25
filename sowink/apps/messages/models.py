from django.contrib.auth.models import User
from django.db import models


class Message(models.Model):
    to_user = models.ForeignKey(User, related_name='messages_sent')
    from_user = models.ForeignKey(User, related_name='messages_received')
    msg = models.TextField()
    date = models.DateTimeField(auto_now_add=True, blank=True)

    def __unicode__(self):
        return self.to_user.username
