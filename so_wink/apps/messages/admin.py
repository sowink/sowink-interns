from django.contrib import admin

from messages.models import Message


class MsgAdmin(admin.ModelAdmin):
    fields = ['to_user', 'from_user', 'msg']

admin.site.register(Message, MsgAdmin)
