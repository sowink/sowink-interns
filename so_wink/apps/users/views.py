from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

import jingo

from mall.models import UserGift
from messages.models import Message
from users.forms import LoginForm


def login_user(request):
    """Verify user login and password work."""
    msg = []
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect(reverse('users.user_page',
                                                args=[request.user.username]))
                else:
                    msg.append("You have entered a disabled account")
                    return jingo.render(request, 'users/login.html',
                                       {'errors': msg, 'form': form})
        else:
            msg.append("Invalid form")
            return jingo.render(request, 'users/login.html',
                               {'errors': msg, 'form': form})
    else:
        form = LoginForm()
    return jingo.render(request, 'users/login.html',
                       {'errors': msg, 'form': form})


def logout_user(request):
    logout(request)
    return jingo.render(request, 'users/logout.html')


def user_page(request, username):
    """Retrieve username messages and received gifts from database."""
    visitee = get_object_or_404(User, username=username)

    msgs = (Message.objects.filter(to_user__username=username)
         .order_by("-date"))

    gifts = (UserGift.objects.filter(recipient__username=username)
            .order_by("-created"))

    return jingo.render(request, 'users/user_page.html',
                       {'visitee': visitee,
                        'msgs': msgs,
                        'gifts': gifts})
