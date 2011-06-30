from django.conf.urls.defaults import *


urlpatterns = patterns('diary.views',
     url(r'^index$', 'index', name='diary.index'),
     url(r'^list_users$', 'list_users', name='diary.list_users'),
     #url(r'^list/drafts$', 'list_drafts', name='diary.list_drafts'),
     #url(r'^list_users/(?P<username>\w+)$', 'list_diaries', name='diary.list_diaries'),
     url(r'^user/(?P<username>\w+)/$', 'list_diaries', name='diary.list_diaries'),
     url(r'^user/(?P<username>\w+)/entry/(?P<year>\d+)/(?P<month>\d+)/$', 'single', name='diary.single'),
     url(r'^user/(?P<username>\w+)/entry/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', 'single', name='diary.single'),
     url(r'^entry/(?P<diary_id>\d+)/reply$', 'reply', name='diary.reply'),
     url(r'^entry/(?P<diary_id>\d+)/delete$', 'delete', name='diary.delete'),
     url(r'^entry/(?P<diary_id>\d+)/edit$', 'edit', name='diary.edit'),
     url(r'^$', 'personal', name='diary.personal'),
     url(r'^new$', 'new', name='diary.new'),
     url(r'^delete_comment/(?P<comment_id>\d+)$', 'delete_comment', name='diary.delete_comment'),
)
