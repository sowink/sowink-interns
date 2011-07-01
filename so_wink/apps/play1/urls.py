from django.conf.urls.defaults import *


urlpatterns = patterns('play1.views',
     url(r'^$', 'index', name='play1.index'),
)
