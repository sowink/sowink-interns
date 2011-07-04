#NOTE: temporarily pulling parts from other files making this a monolith

from django.http import HttpResponseRedirect

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from django.core.urlresolvers import reverse

from messages.models import Message

import jingo


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

#NOTE: pulled from kitsune users.utils
def handle_register(request, email_template=None, email_subject=None,
                    email_data=None):
    """Handle to help registration."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form = try_send_email_with_form(
                RegistrationProfile.objects.create_inactive_user,
                form, 'email',
                form.cleaned_data['username'],
                form.cleaned_data['password'],
                form.cleaned_data['email'],
                locale=request.locale,
                email_template=email_template,
                email_subject=email_subject,
                email_data=email_data)
            if not form.is_valid():
                # Delete user if form is not valid, i.e. email was not sent.
                # This is in a POST request and so always pinned to master,
                # so there is no race condition.
                User.objects.filter(email=form.instance.email).delete()
        return form
#end NOTE

def register(request):
    """Register a new user."""
    form = handle_register(request)
    try:
        if form.is_valid():
            return jingo.render(request, 'users/register_done.html')
        return jingo.render(request, 'users/register.html',
                            {'form': form})
    except():
        pass


def user_page(request, username):
    '''
    Gets user name from logged_user session variable.
    Retrieve username messages from database.
    Pass in database results to user_page.html template.
    '''

    try:
        # Verify user exists in database.
        User.objects.get(username=username)
    except User.DoesNotExist:
        print "Requested user page:%s not found" % username

    logged_user = request.user.username
    q = (Message.objects.filter(to_user__username=username)
        .order_by("-date"))

    return jingo.render(request, 'users/user_page.html',
                                 {'username': username,
                                 'logged_user': logged_user,
                                 'q': q})
