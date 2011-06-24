from django.http import HttpResponseRedirect

from django.contrib.auth.models import User

from django.core.urlresolvers import reverse

from django.views.decorators.http import require_POST

from mall.models import Gift, UserGift

import jingo


def list_gifts(request, username):
    '''
    Lists the gifts a user has received by most recent
    date. Pass in database results to list_gifts.html template.
    '''

    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        print "Requested user page:%s not found" % username

    logged_user = request.user.username
    q = Gift.objects.all()
    # change q to gifts, variable change

    return jingo.render(request, 'mall/list_gifts.html',
                                 {'username': username,
                                 'logged_user': logged_user,
                                 'q': q})


@require_POST
def buy_gift(request, username):
    '''
    Handles post data and determines whether a purchasing user
    has enough balance to purchase and send a gift.
    '''

    bought_with = 0

    gift_id = request.POST['gift_id']

    if 'bought_wink' in request.POST:
        bought_with = 1
        # look up user balance in WinkCash, error if not

    if 'bought_coins' in request.POST:
        bought_with = 2
        # look up user balance in coins, error if not

    gift = Gift.objects.get(id=gift_id)
    sender = request.user
    to = User.objects.get(username__exact=username)

    entry = UserGift(gift=gift, creator=sender, recepient=to,
                     bought_with=bought_with)
    entry.save()

    return HttpResponseRedirect(reverse('users.user_page',
                                         args=[username]))
