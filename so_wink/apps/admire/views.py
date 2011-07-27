import jingo
import bleach
import urllib # to refresh recaptcha
import random

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
    ctx = {
        'users_list' : User.objects.exclude(username = request.user),
    }
    return jingo.render(request, 'admire/index.html', ctx)

#@login_required
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

    # see if A has already admired B
    # returns empty list if no match
    # TODO: multi filter() or singular get() ?
    already_admire = Admire.objects.filter(admirer = admirer, being_admired = being_admired)
    if already_admire:
        created = already_admire[0].created
        already_text = "Sorry, you can't admire %s again. You admired this person on %s" % (being_admired, created)
        return HttpResponse(already_text)

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

    # 1. email being_admired
    try:
        being_admired.email_user(subject = sbj_to_b, message = msg_to_b)
    except:
        return HttpResponse("Emailing being_admired failed")

    return HttpResponse("Your admire has been sent! <a href='/admire/guess/%s'>That person will see this</a>" % ( str(the_admire_id) ) )
    
def guess_result(request, admire_id):
    # get information from id
    the_admire = Admire.objects.get(id = admire_id)
    admirer = str(the_admire.admirer) # must have str() to make check work
    
    # make sure that they have guessed enough times
    times_tried = the_admire.times_tried
    if times_tried < settings.MAX_ADMIRE_TRIES:
        return HttpResponse("Please go back and keep guessing")
    else:
        return HttpResponse("Your admirer is %s" % admirer)


def guess(request, admire_id):
    print "\nInside guess"
    # get information from id
    the_admire = Admire.objects.get(id = admire_id)
    admirer = the_admire.admirer
    being_admired = the_admire.being_admired

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
        if try_left == 0:
            print "YOU HIT MAX"
            try_text = "You have no more tries left."
            text = "If you would like to find out who your admirer is. <a href='/admire/guess_result/%s'>click here</a>" % ( str(admire_id) )
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
            try_text = "You have %d tries left." % ( try_left )

        # TODO: make this relative to MAX_ADMIRE_TRIES
        # check correctness: +mojo 5%, 2nd: 2%, 3rd, 1%
        inc = 0
        if name_chosen == str(admirer):    
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

            # save mojo to database
            print "saving mojo to database:"
            a_b_prof.mojo += inc
            a_b_prof.save()
            b_a_prof.mojo += inc
            b_a_prof.save()

            # email admirer about successful guess
            sbj_to_a = "%s guessed who you are on try %d" % ( str(being_admired), times_tried )
            msg_to_a = "Now you should invite him/her on a date!"
            admirer.email_user(subject = sbj_to_a, message = msg_to_a)

            try_text = "You GOT IT! :D"
            # %% = '%' string interpolation escape
            text = "You and %s's mojo points have increased by %d%%." % ( name_chosen, inc )
            
        ctx = {
            'the_admire': the_admire,
            'try_text' : try_text,
            'result_text' : text
        }
        return jingo.render(request, file, ctx)

    # GET request only -------------------

    # Randomize guesses to display. 1 must be the admirer, not display person itself
    # 1. delete the a from list 
    # 2. delete the b from list 
    guess_qset = User.objects.exclude(username = admirer)
    guess_qset = guess_qset.exclude(username = str(being_admired) )
    # 3. randomize and take first 5 and list-ify 
    num_fillers = settings.NUMBER_GUESSES_DISPLAYED - 1
    guess_list = list(guess_qset.order_by('?')[:num_fillers])
    # 4. add a into list
    guess_list.append( admirer )
    # 5. shuffle list again
    random.shuffle(guess_list)

    # template stuff
    first_try_text = "You have %s tries " % ( settings.MAX_ADMIRE_TRIES )

    file = 'admire/guess.html'
    ctx = {
        'the_admire': the_admire,
        'number': 3,
        'first_try_text' : first_try_text,
        'users_list' : guess_list,
    }
    return jingo.render(request, file, ctx)
