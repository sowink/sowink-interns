from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('messages.utils',
    url(r'^send_message/$', 'send_message', name='messages.send_message'),
)
