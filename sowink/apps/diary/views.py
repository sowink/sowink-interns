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


def index(request):
    """This view displays navigation for the diary.


    It is simply a copy of the navigation bar that is in every diary page.
    """
    data = {}
    return jingo.render(request, 'diary/home.html', data)
    

def list_diaries(request, username):
    """Lists the diaries belonging to username. If the username is the
    currently logged in user displays private diaries too. If it is another
    user's page it only displays non-draft, non-private entries.   """
    user = get_object_or_404(User, username=username)
    thedate = datetime.datetime.today()
    try:
        year = int(request.GET.get('year', thedate.year))
        month = int(request.GET.get('month', thedate.month))
    except ValueError:
        year = thedate.year
        month = thedate.month
    if month <= 0:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1
    # create a list of days in month to iterate through
    days_in_month = range(1, calendar.monthrange(year, month)[1] + 1)
    if request.user.username != username:
        diaries = user.diaries.filter(created__year=year,
                                      created__month=month,
                                      is_private=False,
                                      is_draft=False)
    else:
       diaries = user.diaries.filter(created__year=year,
                                  created__month=month,
                                  is_draft=False)
    diaries_dict = {}
    for diary in diaries:
        diaries_dict[diary.created.day] = diary
    # for diary in diaries:
    #     diaries_dict[diary.created.day] = diary.pk
    data = {'curr_user' : user,
            'monthdays' : days_in_month,
            'diaries' : diaries,
            'diaries_dict' : diaries_dict,
            'month' : month,
            'year' : year,
           }
    return jingo.render(request, 'diary/diary_list.html', data)


def list_users(request):
    """Displays a list of users to view their diary. """
    all_users = User.objects.all()
    data = {'users' : all_users} 
    return jingo.render(request, 'diary/diary_users.html', data)


@login_required
def list_drafts(request):
    """ Lists the drafts that the current user has. """
    user = request.user
    # need to refactor this code with list_diaries
    thedate = datetime.datetime.today()
    try:
        year = int(request.GET.get('year', thedate.year))
        month = int(request.GET.get('month', thedate.month))
    except ValueError:
        year = thedate.year
        month = thedate.month
    if month <= 0:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1
    days_in_month = range(1, calendar.monthrange(year, month)[1] + 1)
    diaries = user.diaries.filter(created__year=year,
                                  created__month=month,
                                  is_draft=True)
    diaries_dict = {}
    for diary in diaries:
        diaries_dict[diary.created.day] = diary 
    data = {'curr_user' : user,
            'diaries' : diaries, # can be removed, left for testing
            'monthdays' : days_in_month,
            'diaries_dict' : diaries_dict,
            'month' : month,
            'year' : year,
           }
    return jingo.render(request, 'diary/draft_list.html', data)


@login_required
@require_http_methods(['GET', 'POST'])
def new(request):
    """Create a new diary entry for today. 
    """
    # If they already have a diary for today, redirect them to edit
    thedate = datetime.datetime.today()
    diaries = request.user.diaries.filter(created__year=thedate.year,
                        created__month=thedate.month,
                        created__day=thedate.day)
    if diaries:
        return edit(request, diaries[0].pk)

    if request.method == 'POST':
        form = DiaryForm(request.POST)
        if form.is_valid():
            new_diary = form.save(commit=False)
            new_diary.creator = request.user
            new_diary.created = datetime.datetime.now()
            new_diary.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse('diary.views.view_diary', 
                                                args=[new_diary.pk]))
    else:
        form = DiaryForm(initial={'creator': request.user,
                                       'text': 'Start Typing Here',
                                       'created': datetime.datetime.now(),
                                       'is_draft': True,
                                       'is_private': False,
                                  })
    data = {'diaryform' : form}
    return jingo.render(request,
                        'diary/new_diary.html',
                        data, )


@login_required
def edit(request, diary_id):
    """Edit an existing diary view.
    
       Checks and adds errors for setting a non-draft diary
       to a draft diary.
    """
    entry = get_object_or_404(Diary, pk=diary_id)
    if (entry.creator != request.user):
        raise PermissionDenied()
    if request.method == 'POST':
        diaryform = DiaryForm(request.POST)
        if diaryform.is_valid():
            temp_entry = diaryform.save(commit=False)
            if not entry.is_draft and temp_entry.is_draft:
                diaryform._errors["is_draft"] = diaryform.error_class(
                               [u"Cannot set a published diary to a draft"])
            else:
                entry.text = temp_entry.text
                entry.created = datetime.datetime.now()
                entry.is_draft = temp_entry.is_draft
                entry.is_private = temp_entry.is_private
                entry.save()
            # form.save_m2m()
                return HttpResponseRedirect(reverse('diary.views.view_diary',
                                    args=[diary_id]))
    else:
        diaryform = DiaryForm(instance=entry)
    data = {'diaryform': diaryform,
            'diary': entry}
    return jingo.render(request, 'diary/edit_diary.html', data)


@login_required
def reply(request, diary_id):
    """ Adds a comment to a diary entry where pk=diary_id. """
    entry = get_object_or_404(Diary, pk=diary_id)
    if entry.creator != request.user and (entry.is_private or entry.is_draft):
        raise PermissionDenied()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.diary = entry
            new_comment.creator = request.user
            new_comment.created = datetime.datetime.now()
            new_comment.save()
            form.save_m2m()
    return HttpResponseRedirect(reverse('diary.views.view_diary',
                                        args=[diary_id]))

 
@login_required
def personal(request):
    # diaries = request.user.diaries.all()
    # diaries = request.user.diaries.filter(is_draft=False)
    # data = {'published_diaries' : diaries,
    #        'draft_diaries' : diaries}
    #return jingo.render(request, 'diary/diary_mydiaries.html', data)
   return list_diaries(request, username=request.user.username)


def view_diary(request, diary_id):
    """ View a diary page with pk=diary_id. """
    entry = get_object_or_404(Diary, pk=diary_id)
    # If not owner, deny access to private or draft entries
    if entry.creator != request.user and (entry.is_private or entry.is_draft):
        raise PermissionDenied()

    comments = entry.comments.all()
    diary_form = DiaryForm(instance=entry)
    comment_form = CommentForm()
    data = {'diary' : diary_form,
            'comment_form' : comment_form,
            'entry' : entry,
            'comments' : comments,
           }
    if entry.creator == request.user:
        data['userbool'] = True
    return jingo.render(request, 'diary/viewdiary.html', data)


@login_required
def delete(request, diary_id):
    """ Deletes a diary, only if logged in user is the creator. """
    entry = get_object_or_404(Diary, pk=diary_id)
    if entry.creator != request.user:
        raise PermissionDenied()
    entry.delete()
    return index(request)


@login_required
def delete_comment(request, comment_id):
    """ Deletes a comment from a diary.

        Only deletes the comment if the logged in user is the creator of the
        comment or of the diary.
    """
    entry = get_object_or_404(Comment, pk=comment_id)
    diary = entry.diary
    if ( entry.creator == request.user ) or ( diary.creator == request.user ):
        entry.delete()
    else:
        raise PermissionDenied()
    return view_diary(request, diary.pk)
