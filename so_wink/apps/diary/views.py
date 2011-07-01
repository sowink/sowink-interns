import jingo
import datetime
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from diary.models import Diary, Comment
from diary.forms import DiaryForm, CommentForm


def index(request):
    data = {}
    return jingo.render(request, 'diary/home.html', data)
    

def list_diaries(request, username):
    user = get_object_or_404(User, username=username)
    diaries = user.diaries.filter(is_draft=False)
    data = {'curr_user' : user,
            'diaries' : diaries}
    return jingo.render(request, 'diary/diary_list.html', data)


def list_users(request):
    all_users = User.objects.all()
    data = {'users' : all_users} 
    return jingo.render(request, 'diary/diary_users.html', data)


@login_required
def list_drafts(request):
    currpage_user = request.user
    diaries = currpage_user.diaries.filter(is_draft=True)
    data = {'curr_user' : currpage_user,
            'diaries' : diaries}
    return jingo.render(request, 'diary/diary_list.html', data)


@login_required
def new(request):
    if request.method == 'GET':
        new_diaryform = DiaryForm(initial={'creator': request.user,
                                       'text': 'Start Typing Here',
                                       'created': datetime.datetime.now(),
                                       'title': 'Enter title here',
                                       'is_draft': True, })
        data = {'diaryform' : new_diaryform}
        return jingo.render(request,
                        'diary/new_diary.html',
                        data, )
    if request.method == 'POST':
        form = DiaryForm(request.POST)
        if form.is_valid():
            new_diary = form.save(commit=False)
            new_diary.creator = request.user
            new_diary.created = datetime.datetime.now()
            new_diary.save()
            form.save_m2m()
    return HttpResponseRedirect(reverse('diary.views.personal'))


@login_required
def edit(request, diary_id):
    entry = get_object_or_404(Diary, pk=diary_id)
    if (entry.creator == request.user):
        if request.method == 'GET':
            diaryform = DiaryForm(instance=entry)
            data = {'diaryform': diaryform,
                    'diary_id': entry.pk}
            return jingo.render(request, 'diary/edit_diary.html', data)
        if request.method == 'POST':
            diaryform = DiaryForm(request.POST)
            if diaryform.is_valid():
                temp_entry = diaryform.save(commit=False)
                entry.title = temp_entry.title
                entry.text = temp_entry.text
                entry.created = datetime.datetime.now()
                entry.is_draft = temp_entry.is_draft
                entry.save()
                # form.save_m2m()
                return HttpResponseRedirect(reverse('diary.views.view_diary',
                                        args=[diary_id]))
    return index(request)


@login_required
def reply(request, diary_id):
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.diary = get_object_or_404(Diary, pk=diary_id)
            new_comment.creator = request.user
            new_comment.created = datetime.datetime.now()
            new_comment.save()
            form.save_m2m()
    return HttpResponseRedirect(reverse('diary.views.view_diary',
                                        args=[diary_id]))

 
@login_required
def personal(request):
    # diaries = request.user.diaries.all()
    diaries = request.user.diaries.filter(is_draft=False)
    data = {'published_diaries' : diaries,
            'draft_diaries' : diaries}
    return jingo.render(request, 'diary/diary_mydiaries.html', data)


def view_diary(request, diary_id):
    entry = get_object_or_404(Diary, pk=diary_id)
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
    entry = get_object_or_404(Diary, pk=diary_id)
    if entry.creator == request.user:
        entry.delete()
    return index(request)


@login_required
def delete_comment(request, comment_id):
    entry = get_object_or_404(Comment, pk=comment_id)
    diary = entry.diary
    if ( entry.creator == request.user ) or ( diary.creator == request.user ):
        entry.delete()
    return view_diary(request, diary.pk)
