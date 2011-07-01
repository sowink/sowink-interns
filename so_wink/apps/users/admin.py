from django.contrib import admin

from users.models import Profile


class ProfileAdmin(admin.ModelAdmin):
    fields = ['user', 'gender', 'winkcash', 'coins']

admin.site.register(Profile, ProfileAdmin)
