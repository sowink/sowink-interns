import jingo
import datetime
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from diary.models import DiaryForm, CommentForm, Diary

def index(request):
    data = {}  # You'd add data here that you're sending to the template.
    return jingo.render(request, 'diary/home.html', data)
    

def list_diaries(request, user_id):
    currpage_user = get_object_or_404(User, pk=user_id)
    diaries = currpage_user.diaries.filter(is_draft=False)
    data = {'curr_user' : currpage_user,
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
def create_diary(request):
    new_diaryform = DiaryForm(initial={'author': request.user,
                                       'text': 'Start Typing Here',
                                       'creation_date': datetime.datetime.now(),
                                       'title': 'Enter title here',
                                       'is_draft': True, })
    data = {'diaryform' : new_diaryform}
    return jingo.render(request,
                        'diary/edit_diary.html',
                        data,
                       )


@login_required
def save_diary(request):
    if request.method == 'POST':
        form = DiaryForm(request.POST)
        if form.is_valid():
            new_diary = form.save(commit=False)
            new_diary.author = request.user
            new_diary.creation_date = datetime.datetime.now()
            new_diary.save()
            form.save_m2m()
    return HttpResponseRedirect(reverse('diary.views.index'))

@login_required
def save_comment(request, diary_id):
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.diary_entry = get_object_or_404(Diary, diary_id)
            new_comment.commenter = request.user
            new_comment.pub_date = datetime.datetime.now()
            new_comment.save()
            form.save_m2m()
    return HttpResponseRedirect(reverse('diary.views.index'))

 
@login_required
def my_diaries(request):
    diaries = request.user.diaries.all()
    data = {'published_diaries' : diaries,
            'draft_diaries' : diaries}
    return jingo.render(request, 'diary/diary_mydiaries.html', data)


def view_diary(request, diary_id):
    curr_diary = get_object_or_404(Diary, pk=diary_id)
    comments = curr_diary.comments.all()
    diary_form = DiaryForm(instance=curr_diary)
    comment_form = CommentForm()
    data = {'diary' : diary_form,
            'diary_title' : curr_diary.title,
            'diary_text' : curr_diary.text,
            'diary_author' : curr_diary.author,
            'diary_date' : curr_diary.creation_date,
            'comment_form' : comment_form,
            'curr_diary' : curr_diary,
            'comments' : comments,
           }
    if curr_diary.author == request.user:
        data['userbool'] = True
    return jingo.render(request, 'diary/viewdiary.html', data)
