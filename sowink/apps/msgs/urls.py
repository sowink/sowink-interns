from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('msgs.views',
    url(r'^$', 'home', name='examples.home'),
    url(r'^bleach/?$', 'bleach_test', name='examples.bleach'),

    url(r'^login/$', 'login_user', name='msgs.login'),
    url(r'^logout/$', 'logout_user', name='msgs.logout'),
    url(r'^user/(\w+)/$', 'user_page', name='msgs.user-page'),
    url(r'^send-message/$', 'send_message', name='msgs.send-message'),
)
