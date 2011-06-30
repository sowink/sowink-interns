from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('mall.views',
    url(r'^gifts/list/(?P<username>\w+)/$', 'list_gifts',
        name='mall.list_gifts'),
    url(r'^gifts/buy/(?P<username>\w+)/$', 'buy_gift', name='mall.buy_gift'),
)
