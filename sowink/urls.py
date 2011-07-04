from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.views.i18n import javascript_catalog
from django.views.decorators.cache import cache_page

import authority
from waffle.views import wafflejs


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^chat', include('chat.urls')),
    (r'^livechat', include('livechat.urls')),
    (r'^$|^home$', include('play1.urls')),
    #(r'^$|^loginwindow$', 'django.contrib.auth.views.login'),
    (r'^diary/', include('diary.urls')), 
    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^login', include('users.urls')),
    (r'^register', include('users.urls')),

    (r'', include('messages.urls')),
    (r'', include('users.urls')),
    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

#NOTE: kitsune
    # Javascript translations.
    url(r'^jsi18n/.*$', cache_page(60 * 60 * 24 * 365)(javascript_catalog),
        {'domain': 'javascript', 'packages': ['kitsune']}, name='jsi18n'),
    # JavaScript Waffle.
    url(r'^wafflejs$', wafflejs, name='wafflejs'),

    # Services and sundry.
    (r'', include('sumo.urls')),
#end NOTE
)

## In DEBUG mode, serve media files through Django.
if settings.DEBUG:
    # Remove leading and trailing slashes so the regex matches.
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
