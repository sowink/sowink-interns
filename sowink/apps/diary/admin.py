from django.contrib import admin
from diary.models import Diary
from diary.models import Comment


class DiaryAdmin(admin.ModelAdmin):
    fields = ('creator', 'created', 'created_day', 'text', 'is_draft', 'is_private')


admin.site.register(Diary, DiaryAdmin)
admin.site.register(Comment)
