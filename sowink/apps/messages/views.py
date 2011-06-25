from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from messages.models import Message


@require_POST
def send_message(request):
    """
    Sends message to a User with a valid username.
    Retrieves User objects from database and creates
    a Message object in the database. Afterwards, display
    message on commented page.
    """

    to = request.POST['usr']
    to_who = get_object_or_404(User, username=to)
    frm_who = request.user
    msg = request.POST['message']

    entry = Message.objects.create(to_user=to_who, from_user=frm_who, msg=msg)

    return HttpResponseRedirect(reverse('users.user_page',
                                         args=[to]))
