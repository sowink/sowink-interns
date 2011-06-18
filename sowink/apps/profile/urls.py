from django.conf.urls.defaults import patterns  # , include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('profile.views',
    (r'^$', 'index'),
    (r'^(?P<profile_id>\d+)/$', 'view_profile'),
    (r'^(?P<profile_id>\d+)/sendmessage/$', 'send_message'),
)
