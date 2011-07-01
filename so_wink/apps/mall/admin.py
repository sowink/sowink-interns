from django.contrib import admin

from mall.models import Gift, UserGift


class GiftAdmin(admin.ModelAdmin):
    fields = ['title', 'image', 'creator', 'winkcash', 'coins']


class UserGiftAdmin(admin.ModelAdmin):
    fields = ['gift', 'creator', 'recipient', 'bought_with']

admin.site.register(Gift, GiftAdmin)
admin.site.register(UserGift, UserGiftAdmin)
