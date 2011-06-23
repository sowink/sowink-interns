from messages.models import Message
from django.contrib import admin


class MsgAdmin(admin.ModelAdmin):
    fields = ['to_user', 'from_user', 'msg']

admin.site.register(Message, MsgAdmin)
