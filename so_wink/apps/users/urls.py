from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('users.views',
    url(r'^login/$', 'login_user', name='users.login'),
    url(r'^logout/$', 'logout_user', name='users.logout'),
    url(r'^profile/user/(?P<username>\w+)/$', 
        'user_page', name='users.user_page'),
)
