from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('mall.views',
    url(r'^mall/gifts/list/(?P<username>\w+)/$', 'list_gifts',
        name='mall.list_gifts'),
    url(r'^mall/gifts/buy/(?P<username>\w+)/$', 'buy_gift', 
        name='mall.buy_gift'),
)
