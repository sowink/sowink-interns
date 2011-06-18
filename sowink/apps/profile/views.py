from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect  # , HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
#from django.contrib.auth.views import logout_then_login
import re
import datetime
from profile.models import Profile  # , Message
from profile.forms import MessageForm


def index(request):
    p_list = Profile.objects.all()
    return render_to_response('profile/index.html', {'profile_list': p_list, })


@login_required
def login(request):
    pass


def view_profile(request, profile_id):
    #return HttpResponse("You're viewing profile: %s." % profile_id)
    form = MessageForm()
    currusername = request.user
    currpage_profile = get_object_or_404(Profile, pk=profile_id)
    try:
        currlogin_profile = get_object_or_404(Profile, username=currusername)
    except:
        currlogin_profile = None
    messages = currpage_profile.filter_messages(currlogin_profile)
    return render_to_response('profile/view_profile.html',
                              {'profile': currpage_profile,
                              'uname': currusername,
                              'messages': messages,
                              'form': form},
                              context_instance=RequestContext(request))


@login_required
def send_message(request, profile_id):
    form = MessageForm(request.POST)
    if form.is_valid():
        sent_message = form.cleaned_data['message']
    else:
        sent_message = ''
    p = get_object_or_404(Profile, pk=profile_id)
   #try:
   #   sent_message = request.POST['messagetext']
   #except:
   #   sent_message = ''
   #if len(sent_message) == 0:
    if re.search(r'^\s*$', sent_message):
        return render_to_response('profile/view_profile.html',
                         {'profile': p,
                         'error_message': "Please provide a message.",
                         },
                         context_instance=RequestContext(request))
    p.message_set.create(from_user=Profile.objects.get(username=request.user),
                         pub_date=datetime.datetime.now(),
                         content=sent_message)
    p.save()
    return HttpResponseRedirect(reverse('profile.views.view_profile',
                                        args=(p.id,)))
