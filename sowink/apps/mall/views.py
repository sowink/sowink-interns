from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

import jingo

from mall.models import Gift, UserGift


def list_gifts(request, username):
    """ 
    Lists the gifts a user has received by most recent
    date. Pass in database results to list_gifts.html template.
    """

    # Verify user exists
    get_object_or_404(User, username=username)

    logged_user = request.user.username
    gifts = Gift.objects.all()

    return jingo.render(request, 'mall/list_gifts.html',
                                 {'username': username,
                                 'logged_user': logged_user,
                                 'gifts': gifts})


@require_POST
def buy_gift(request, username):
    """
    Handles post data and determines whether a purchasing user
    has enough balance to purchase and send a gift.
    """

    gift_id = request.POST['gift_id']

    gift = get_object_or_404(Gift, id=gift_id)
    to = get_object_or_404(User, username=username)
    bought_with = 1 if 'bought_wink' in request.POST else 2

    entry = UserGift.objects.create(gift=gift, creator=request.user, 
                                    recepient=to, bought_with=bought_with)
    #entry.save()

    return HttpResponseRedirect(reverse('users.user_page',
                                         args=[username]))
