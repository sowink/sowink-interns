import datetime
from diary.models import Diary
from django.shortcuts import get_object_or_404


def diary_date(year=None, month=None):
    today = datetime.datetime.today()
    try:
        year, month = int(year), int(month)
    # If year, month is None or not an int set the date to today
    except (ValueError, TypeError):
        year = today.year
        month = today.month
    return (year or today.year,
            max(min(month, 12), 1) if month else today.month)


def entries_for_user_month(user, year=None, month=None, **kwargs):
    year, month = diary_date(year, month)
    return user.diaries.filter(created__year=year, created__month=month, **kwargs).order_by('-created')


def get_kwargs_for_diary_id(diary_id):
    diary = get_object_or_404(Diary, pk=diary_id)
    return {'year': diary.created.year,
            'username': diary.creator.username,
            'month': diary.created.month,
            'day': diary.created.day}
