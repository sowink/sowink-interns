from django.http import HttpResponseRedirect

from django.contrib.auth.models import User

from django.core.urlresolvers import reverse

from django.views.decorators.http import require_POST

from messages.models import Message


@require_POST
def send_message(request):
    '''
    Sends message to a User with a valid username.
    Retrieves User objects from database and creates
    a Message object in the database. Afterwards, display
    message on commented page.
    '''
    to = request.POST['usr']
    frm = request.session['logged_user']
    to_who = User.objects.get(username__exact=to)
    frm_who = User.objects.get(username__exact=frm)
    msg = request.POST['message']

    entry = Message(to_user=to_who, from_user=frm_who, msg=msg)
    entry.save()

    return HttpResponseRedirect(reverse('users.user_page',
        args=[to]))
