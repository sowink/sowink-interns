from django.conf.urls.defaults import *


urlpatterns = patterns('diary.views',
     url(r'^$', 'index', name='diary.index'),
)
