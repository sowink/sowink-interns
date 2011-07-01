from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('messages.views',
    url(r'^send_message/$', 'send_message', name='messages.send_message'),
)
