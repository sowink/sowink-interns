from mall.models import Gift, UserGift
from django.contrib import admin


class GiftAdmin(admin.ModelAdmin):
    fields = ['title', 'creator', 'winkcash', 'coins']


class UserGiftAdmin(admin.ModelAdmin):
    fields = ['gift', 'creator', 'recepient', 'bought_with']

admin.site.register(Gift, GiftAdmin)
admin.site.register(UserGift, UserGiftAdmin)
