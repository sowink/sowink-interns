from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib.auth.views import login as auth_login_view

from . import views

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('admire.views', # gets information from views.py

    url(r'^$', views.index, name="admire.index"), # goes to views.py's "def index"
    url(r'^email/(?P<b_name>\w+)', views.email, name="admire.email"),
    url(r'^guess/(?P<user_name>\w+)', views.guess, name="admire.guess"), 
)

## In DEBUG mode, serve media files through Django.
if settings.DEBUG:
    # Remove leading and trailing slashes so the regex matches.
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
