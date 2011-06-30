from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

import jingo

from mall.forms import BuyGiftForm
from mall.models import Gift


def list_gifts(request, username):
    """Lists all gifts a user has received by the most recent date."""
    visitee = get_object_or_404(User, username=username)
    gifts = Gift.objects.all()
    form = BuyGiftForm()

    return jingo.render(request, 'mall/list_gifts.html',
                                 {'visitee': visitee,
                                  'gifts': gifts,
                                  'form': form})


@require_POST
def buy_gift(request, username):
    """Handles form POST data and determines whether purchase can be made."""
    bought_with = 1 if 'bought_wink' in request.POST else 2

    form = BuyGiftForm(bought_with=bought_with, data=request.POST)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('users.user_page',
                                             args=[username]))
    else:
        # TODO: implement to add errors to display
        # currently, User is sent back to the mall
        form = BuyGiftForm()

    return HttpResponseRedirect(reverse('mall.list_gifts', args=[username]))
