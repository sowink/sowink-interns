from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

import jingo

from mall.models import UserGift
from messages.models import Message


def login_user(request):
    '''
    Login user and store username in logged_user session variable.
    After authentication redirect logged_user to their homepage.
    '''

    msg = []
    if request.method == 'POST':
        usr = request.POST['usr']
        psswd = request.POST['psswd']
        user = authenticate(username=usr, password=psswd)
        if user is not None:
            if user.is_active:
                login(request, user)
                request.session['logged_user'] = usr
                return HttpResponseRedirect(reverse('users.user_page',
                    args=[usr]))
            else:
                msg.append("You have entered a disabled account")
        else:
            msg.append("Invalid login")
    return jingo.render(request, 'users/login.html', {'errors': msg})


def logout_user(request):
    '''
    Logs out user and deletes logged_user session variable.
    '''

    try:
        del request.session['logged_user']
    except KeyError:
        pass
    logout(request)
    return jingo.render(request, 'users/logout.html')


def user_page(request, username):
    '''
    Gets user name from logged_user session variable.
    Retrieve username messages from database.
    Pass in database results to user_page.html template.
    '''

    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        print "Requested user page:%s not found" % username

    logged_user = request.user.username
    msgs = (Message.objects.filter(to_user__username=username)
         .order_by("-date"))

    gifts = (UserGift.objects.filter(recepient__username=username)
            .order_by("-created"))

    return jingo.render(request, 'users/user_page.html',
                                 {'username': username,
                                  'logged_user': logged_user,
                                  'msgs': msgs,
                                  'gifts': gifts})
