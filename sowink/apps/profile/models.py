from django.db import models
#from django.contrib import admin

# Create your models here.


class Profile(models.Model):
    username = models.CharField(max_length=200)

    def __unicode__(self):
        return self.username

    def filter_messages(self, currlogin_profile):
        try:
            if currlogin_profile.username == self.username:
                messages = self.message_set.all()
            else:
                messages = Message.objects.filter(profile_page=self,
                                                 from_user=currlogin_profile)
        except:
            messages = []
        return messages


class Message(models.Model):
    profile_page = models.ForeignKey(Profile)  # , related_name='reciever')
    from_user = models.ForeignKey(Profile, related_name='sender')
    pub_date = models.DateTimeField('date published')
    content = models.CharField(max_length=2000)

    def __unicode__(self):
        return self.content[:200]
