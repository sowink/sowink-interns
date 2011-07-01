from django.conf.urls.defaults import *


urlpatterns = patterns('diary.views',
     url(r'^index$', 'index', name='diary.index'),
     url(r'^list_users$', 'list_users', name='diary.list_users'),
     url(r'^list/drafts$', 'list_drafts', name='diary.list_drafts'),
     url(r'^list_users/(?P<username>\w+)$', 'list_diaries', name='diary.list_diaries'),
     url(r'^entry/(?P<diary_id>\d+)/reply$', 'reply', name='diary.reply'),
     url(r'^$', 'personal', name='diary.my_diaries'),
     url(r'^viewdiary/(?P<diary_id>\d+)$', 'view_diary', name='diary.view_diary'),
     url(r'^new$', 'new', name='diary.create_diary'),
     url(r'^edit/(?P<diary_id>\d+)$', 'edit', name='diary.edit'),
     url(r'^delete/(?P<diary_id>\d+)$', 'delete', name='diary.delete'),
     url(r'^delete_comment/(?P<comment_id>\d+)$', 'delete_comment', name='diary.delete_comment'),
)
