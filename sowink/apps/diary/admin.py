from django.contrib import admin
from diary.models import Diary
from diary.models import Comment


class DiaryAdmin(admin.ModelAdmin):
    fields = ['title', 'author', 'creation_date', 'text', 'is_draft']


admin.site.register(Diary)
admin.site.register(Comment)
