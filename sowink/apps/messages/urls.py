from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('messages.views',
    url(r'^$', 'home', name='examples.home'),
#    url(r'^bleach/?$', 'bleach_test', name='examples.bleach'),

    url(r'^login/$', 'login_user', name='messages.login'),
    url(r'^logout/$', 'logout_user', name='messages.logout'),
    url(r'^profile/user/(\w+)/$', 'user_page', name='messages.user-page'),
    url(r'^send-message/$', 'send_message', name='messages.send-message'),
)
