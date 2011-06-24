from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('mall.views',
    url(r'^mall/gifts/list/(\w+)/$', 'list_gifts', name='mall.list_gifts'),
    url(r'^mall/gifts/buy/(\w+)/$', 'buy_gift', name='mall.buy_gift'),
   # url(r'^login/$', 'login_user', name='users.login'),
    #url(r'^logout/$', 'logout_user', name='users.logout'),
#    url(r'^profile/user/(\w+)/$', 'user_page', name='users.user_page'),
)
