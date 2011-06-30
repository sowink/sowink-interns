import jingo
import datetime
import calendar

from django.views.decorators.http import require_http_methods, require_GET
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied

from diary.models import Diary, Comment
from diary.forms import DiaryForm, CommentForm
from diary.utils import entries_for_user_month, diary_date, get_kwargs_for_diary_id


def index(request):
    """This view displays navigation for the diary.

    It is simply a copy of the navigation bar that is in every diary page.

    """
    data = {}
    return jingo.render(request, 'diary/home.html', data)
    

def list_diaries(request, username):
    """Lists the diaries belonging to username.
      
    If the username is the currently logged in,
    user displays private diaries too.
    If it is another user's page it only displays non-draft,
    non-private entries.
    
    """
    user = get_object_or_404(User, username=username)
    diaries = user.diaries.order_by('-created')[:5]

    data = {
            'diaries' : diaries,
           }
    return jingo.render(request, 'diary/diary_list.html', data)


def list_users(request):
    """Displays a list of users to view their diary. """
    all_users = User.objects.all()
    data = {'users' : all_users} 
    return jingo.render(request, 'diary/diary_users.html', data)


@login_required
@require_http_methods(['GET', 'POST'])
def new(request):
    """Create a new diary entry for today."""
    today = datetime.datetime.today()
    diaries = request.user.diaries.filter(created__year=today.year,
                        created__month=today.month,
                        created__day=today.day)
    # If they already have a diary for today, redirect them to edit
    if diaries:
        return HttpResponseRedirect(reverse('diary.views.edit',
                                             args=[diaries[0].pk]))
    if request.method == 'POST':
        form = DiaryForm(creator=request.user, data=request.POST)
        if form.is_valid():
            entry = form.save()
            return HttpResponseRedirect(reverse('diary.views.single',
                                    kwargs=get_kwargs_for_diary_id(entry.pk)))
    else: # request.method == 'GET'
        form = DiaryForm(creator=request.user, 
                         initial={'text': 'Start Typing Here'})
    data = {'diaryform' : form}
    return jingo.render(request,
                        'diary/new_diary.html',
                        data)


@login_required
def edit(request, diary_id):
    """Edit an existing diary view.
    
    Checks and adds errors for setting a non-draft diary
    to a draft diary.

    """
    entry = get_object_or_404(Diary, pk=diary_id)
    if (entry.creator != request.user):
        raise PermissionDenied
    if request.method == 'POST':
        diaryform = DiaryForm(creator=entry.creator, data=request.POST,
                              instance=entry)
        if diaryform.is_valid():
            diaryform.save()
            return HttpResponseRedirect(reverse('diary.views.single',
                                    kwargs=get_kwargs_for_diary_id(entry.pk)))
    else:
        diaryform = DiaryForm(creator=entry.creator, instance=entry)
    data = {'diaryform': diaryform,
            'diary': entry}
    return jingo.render(request, 'diary/edit_diary.html', data)


@login_required
def reply(request, diary_id):
    """Adds a comment to a diary entry where pk=diary_id."""
    entry = get_object_or_404(Diary, pk=diary_id)
    if entry.creator != request.user and (entry.is_private or entry.is_draft):
        raise PermissionDenied()
    if request.method == 'POST':
        form = CommentForm(creator=request.user, diary=entry, data=request.POST)
        if form.is_valid():
            form.save()
    return HttpResponseRedirect(reverse('diary.views.single',
                                     kwargs=get_kwargs_for_diary_id(entry.pk)))

 
@login_required
def personal(request):
   return list_diaries(request, username=request.user.username)


def single(request, username, year=None, month=None, day=None):
    """View a diary page with pk=diary_id."""
    today = datetime.date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month
    user = get_object_or_404(User, username=username)
    year, month = diary_date(year,
                             month)
    # Create a list of days in the month
    days_in_month = range(1, calendar.monthrange(year, month)[1] + 1)
    if request.user.username != username:
        diaries = entries_for_user_month(user,
                           year,
                           month,
                           is_private=False,
                           is_draft=False)
    else:
        diaries = entries_for_user_month(user,
                           year,
                           month)
    if not day:
        day = diaries[0].created.day if diaries else today.day
        # add redirect here to update url?

    diaries_dict = {}
    for diary in diaries:
        diaries_dict[diary.created.day] = diary

    try:
        entry = Diary.objects.get(creator__username=username,
                                  created__year=year,
                                  created__month=month,
                                  created__day=day)
    except Diary.DoesNotExist:
        entry = None
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    if year == today.year:
        months = months[:today.month]
    data = {'months': months,
            'monthdays': days_in_month,
            'diaries_dict': diaries_dict,
            'month': month,
            'year': year,
            'entry': entry,
            'username': username
           }
    if entry:                             
        # If not owner, deny access to private or draft entries
        if entry.creator != request.user and (entry.is_private or entry.is_draft):
            raise PermissionDenied
        data['comments'] = entry.comments.all()
        data['diary'] = DiaryForm(creator=entry.creator, instance=entry)
        data['comment_form'] = CommentForm(creator=request.user, diary=entry)
    return jingo.render(request, 'diary/single.html', data)


@login_required
def delete(request, diary_id):
    """ Deletes a diary, only if logged in user is the creator. """
    entry = get_object_or_404(Diary, pk=diary_id)
    entry_creator = entry.creator
    if entry_creator != request.user:
        raise PermissionDenied
    entry.delete()
    return HttpResponseRedirect(reverse('diary.views.list_diaries',
                                           args=[entry_creator.username]))


@login_required
def delete_comment(request, comment_id):
    """ Deletes a comment from a diary.

        Only deletes the comment if the logged in user is the creator of the
        comment or of the diary.

    """
    entry = get_object_or_404(Comment, pk=comment_id)
    diary = entry.diary
    if ( entry.creator != request.user ) and ( diary.creator != request.user ):
        raise PermissionDenied
    entry.delete()
    return HttpResponseRedirect(reverse('diary.views.single',
                                           kwargs=get_kwargs_for_diary_id(diary.pk)))
