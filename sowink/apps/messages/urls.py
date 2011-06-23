from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('messages.views',
    url(r'^send-message/$', 'send_message', name='messages.send-message'),
)
