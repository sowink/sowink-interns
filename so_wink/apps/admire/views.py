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
from django.conf import settings
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
    return jingo.render(request, 'admire/index.html', ctx)

def email(request, b_name):
    admirer = ""
    being_admired = ""
    the_admire_id = ""

    # get admirer
    try:
        admirer = User.objects.get(username = request.user)
    except User.DoesNotExist:
        return HttpResponse("Invalid admirer username. Have you logged in?")

    # get being_admired
    try:
        being_admired = User.objects.get(username = b_name)
    except User.DoesNotExist:
        return HttpResponse("Invalid being_admired username")

    # put Admire in database
    try:
        the_admire = Admire.objects.create(admirer = admirer, being_admired = being_admired)
        the_admire_id = the_admire.id
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

    return HttpResponse("Your admire has been sent! <a href='/admire/guess/" + str(the_admire_id) + "'>That person will see</a>")
    
def guess_result(request, admire_id):
    # get information from id
    the_admire = Admire.objects.get(id = admire_id)
    admirer = str(the_admire.admirer) # must have str() to make check work
    
    # make sure that they have guessed enough times
    times_tried = the_admire.times_tried
    if times_tried < settings.MAX_ADMIRE_TRIES:
        return HttpResponse("Please go back and keep guessing")
    else:
        return HttpResponse("Your admirer is " + admirer)


def guess(request, admire_id):
    print "\nInside guess"

    # get information from id
    the_admire = Admire.objects.get(id = admire_id)
    admirer = str(the_admire.admirer) # must have str() to make check work
    being_admired = str(the_admire.being_admired)

    if request.method == "POST":
        file = 'admire/guess_results.html'
        # default text
        text = "haha"

        print "inside post"
        # Get input for guessed admirer
        user_input = request.POST
        name_chosen = user_input['nameClicked']

        # increment times tried
        the_admire.times_tried += 1
        the_admire.save()

        # check if already correct
        if the_admire.got_right:
            # TODO: disable voting
            try_text = "Great job!"
            text = "You already guessed correctly!"
            ctx = {
                'try_text' : try_text,
                'result_text' : text
            }
            return jingo.render(request, file, ctx)

        # check tried bounds
        times_tried = the_admire.times_tried
        try_left = settings.MAX_ADMIRE_TRIES - times_tried
        print times_tried
        if try_left == 0:
            print "YOU HIT MAX"
            try_text = "You have no more tries left."
            text = "If you would like to find out who your admirer is. <a href='/admire/guess_result/" + str(admire_id) + "'>click here</a>"
        elif try_left < 0:
            print "REALLY BAD!"
            # TODO: disable voting
            try_text = "Stop messing with the system, you really have no more tries left"
            text = "You did not guess correctly."
            ctx = {
                'try_text' : try_text,
                'result_text' : text
            }
            return jingo.render(request, file, ctx)
        elif try_left == 1:
            try_text = "You have 1 try left."
        else: # could be 2, 3 ... MAX_ADMIRE_TRIES-1
            try_text = "You have " + str(try_left) + " tries left."

        # TODO: make this relative to MAX_ADMIRE_TRIES
        # check correctness: +mojo 5%, 2nd: 2%, 3rd, 1%
        inc = 0
        print "4p"
        if name_chosen == admirer:    
            # record it
            the_admire.got_right = True
            the_admire.save() 

            if times_tried == 1:
                inc = 5
            elif times_tried == 2:
                inc = 2
            elif times_tried == 3:
                inc = 1
 
            # get information from profilevisit
            a_b_prof = ProfileVisit.objects.get( visited_user = the_admire.admirer_id, visitor = the_admire.being_admired_id )
            b_a_prof = ProfileVisit.objects.get( visited_user = the_admire.being_admired_id, visitor = the_admire.admirer_id )
            print "the 2 prof ids:"
            print a_b_prof.id
            print b_a_prof.id

            # save mojo to database
            print "saving mojo to database:"
            a_b_prof.mojo += inc
            print a_b_prof.mojo
            a_b_prof.save()
            b_a_prof.mojo += inc
            b_a_prof.save()

            try_text = "You GOT IT! :D"
            text = "You and " + name_chosen + "'s mojo points have increased by " + str(inc) + "%."
            
        ctx = {
            'try_text' : try_text,
            'result_text' : text
        }
        return jingo.render(request, file, ctx)

    # GET request only -------------------

    first_try_text = "You have " + str(settings.MAX_ADMIRE_TRIES) + " tries."

    file = 'admire/guess.html'
    ctx = {
        'first_try_text' : first_try_text,
        'users_list' : User.objects.all(),
    }
    return jingo.render(request, file, ctx)
