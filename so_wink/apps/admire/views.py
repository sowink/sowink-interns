import jingo
import bleach
import urllib # to refresh recaptcha

from commons.urlresolvers import reverse

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.shortcuts import render_to_response, get_object_or_404
from django.db import connection, transaction
from django.utils import simplejson
import json

from django.contrib.auth.models import User


# urls.py's views. It renders the urls by putting in appropriate values into templates
# each def 
#       - corresponds to a template's html
#       - must return a HttpResponse. Simplest one is `return HttpResponse("Hello World!")`

# The dictionary maps keys for the template's {{ matching_key }} to its value. 
# The key/value can be for a list, because in the template, there is a for loop that goes through each value of the list.
#       e.g. index's Page.objects.all() is a list of all page (xss, sqlinjection)s

def index(request):
    print "^ ^ ^ ^ ^ Welcome to the Index Page ^ ^ ^ "
    print "request.user: "
    print request.user
    ctx = {
        'users_list' : User.objects.all(),
    }
    rendered = jingo.render(request, 'admire/index.html', ctx)
    return rendered

def email(request, user_name):
    print user_name

    # get user
    try:
        user = User.objects.get(username = user_name)
    except User.DoesNotExist:
        return HttpResponse("Invalid username")

    # email user
    try:
        user.email_user(subject="HaoQi Test Django Email", message="Haoqi :D:D:D:D")
    except:
        return HttpResponse("Failed to email")

    print "hiiiiiiiii"
    return HttpResponse("Your admire has been sent! <a href='/admire/guess/" + user_name + "'>That person will see</a>")
    
#from django.views.decorators.csrf import csrf_protect
#@csrf_protect
def guess(request, user_name):
    print user_name
    if request.method == "POST":
        print "GGGGGGGGGGPPPPPPPPPPPPPPPPPPPPP"

    ctx = {
        'users_list' : User.objects.all(),
    }
    rendered = jingo.render(request, 'admire/guess.html', ctx)
    return rendered
