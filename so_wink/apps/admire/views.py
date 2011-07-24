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

from admire.models import Admire, ProfileVisit


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

def email(request, b_name):
    admirer = ""
    being_admired = ""

    # get admirer
    try:
        admirer = User.objects.get(username = request.user)
    except User.DoesNotExist:
        return HttpResponse("Invalid admirer username")

    # get being_admired
    try:
        being_admired = User.objects.get(username = b_name)
    except User.DoesNotExist:
        return HttpResponse("Invalid being_admired username")

    # put Admire in database
    try:
        Admire.objects.create(admirer = admirer, being_admired = being_admired)
    except:
        return HttpResponse("failed to record admire in database.")

    # email users 
    # TODO: put messages in database?
    sbj_to_b = "You got an Admirer! Guess who!"
    msg_to_b = "You got an admirer. click here to find out who" # TODO: add url

    sbj_to_a_success = "Your Admire was successfully sent. Click to track."
    msg_to_a_success = "You can click on this link to see if " + b_name + " has guessed who you are. We will also email you when b starts to guess you."

    sbj_to_a_fail = "There was a problem and your Admire was not sent. Please try again later."
    msg_to_a_fail = "Sorry about that"

    # 1. email being_admired
    try:
        being_admired.email_user(subject = sbj_to_b, message = msg_to_b)

        # 2. email admirer -- success
        try:
            admirer.email_user(subject = sbj_to_a_success, message = msg_to_a_success)
        except:
            return HttpResponse("Email failed")
    except:
        # 2. email admirer -- fail
        try:
            admirer.email_user(subject = sbj_to_a_fail, message = msg_to_a_fail)
        except:
            return HttpResponse("Email failed")
       
        return HttpResponse("Email failed")

    return HttpResponse("Your admire has been sent! <a href='/admire/guess/" + b_name + "'>That person will see</a>")
    
def guess(request, user_name):
    print user_name
    if request.method == "POST":
        print "GGGGGGGGGGPPPPPPPPPPPPPPPPPPPPP"

    ctx = {
        'users_list' : User.objects.all(),
    }
    rendered = jingo.render(request, 'admire/guess.html', ctx)
    return rendered
