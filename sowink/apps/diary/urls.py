from django.conf.urls.defaults import *


urlpatterns = patterns('diary.views',
     url(r'^$', 'index', name='diary.index'),
     url(r'^list_users$', 'list_users', name='diary.list_users'),
     url(r'^listdrafts$', 'list_drafts', name='diary.list_drafts'),
     url(r'^(?P<user_id>\d+)/$', 'list_diaries', name='diary.list_diaries'),
     url(r'^(?P<diary_id>\d+)/addcomment/$', 'save_comment', name='diary.save_comment'),
     url(r'^mydiary/$', 'my_diaries', name='diary.my_diary'),
     url(r'^viewdiary/(?P<diary_id>\d+)$', 'view_diary', name='diary.my_diary'),
     url(r'^viewdiary/addcomment/(?P<diary_id>\d+)/$', 'save_comment', name='diary.save_comment'),
     url(r'^creatediary/$', 'create_diary', name='diary.create_diary'),
     url(r'^creatediary/processdiaryform/$', 'save_diary', name='diary.save_diary'),
)
