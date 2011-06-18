from profile.models import Message, Profile
from django.contrib import admin


class MessageInline(admin.StackedInline):
    model = Message
    fk_name = 'profile_page'
    extra = 1


class ProfileAdmin(admin.ModelAdmin):
    fields = ['username']
   #fieldsets = [
   #   (None,               {'fields': ['question']}),
   #   ('Date information', {'fields': ['pub_date'], 'classes': ['collapse']}),
   #]
    inlines = [MessageInline]
   #list_display = ('question', 'pub_date', 'was_published_today')
   #list_filter = ['pub_date']
   #search_fields = ['question']
   #date_hierarchy = 'pub_date'


admin.site.register(Profile, ProfileAdmin)
#admin.site.register(Profile)
#admin.site.register(Message)
