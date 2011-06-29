from django.contrib import admin

from users.models import Profile


class ProfileAdmin(admin.ModelAdmin):
    fields = ['user', 'gender', 'wink_cash', 'coins']

admin.site.register(Profile, ProfileAdmin)
