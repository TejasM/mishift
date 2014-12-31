import json
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import DataError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from models import UserProfile, Event

__author__ = 'tmehta'


def login_user(request):
    if request.method == "POST":
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)
        if user is not None:
            # the password verified for the user
            if user.is_active:
                login(request, user)
                return redirect(reverse('dashboard:main'))
            else:
                pass
        else:
            return redirect(reverse('dashboard:login'))
    else:
        if request.user.is_authenticated():
            return redirect(reverse('dashboard:main'))
        return render(request, 'dashboard/login.html')


def sign_up(request):
    if request.method == "POST":
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        organization = request.POST.get('organization', 'UHN')
        qualification = request.POST.get('qualification', 'RN')
        try:
            user = User.objects.create(username=username, email=username, first_name=first_name, last_name=last_name)
            UserProfile.objects.create(user=user, organization=organization, qualification=qualification)
        except DataError:
            return redirect(reverse('dashboard:signup'))
        user.set_password(password)
        user.save()
        user = authenticate(username=username, password=password)
        if user is not None:
            # the password verified for the user
            if user.is_active:
                login(request, user)
                return redirect(reverse('dashboard:main'))
            else:
                pass
        else:
            return redirect(reverse('dashboard:signup'))
    else:
        if request.user.is_authenticated():
            return redirect(reverse('dashboard:main'))
        return render(request, 'dashboard/sign_up.html')


@login_required()
def main(request):
    context = {}
    if request.user.userprofile.is_admin:
        context['employees'] = UserProfile.objects.filter(
            organization=request.user.userprofile.organization, role='employee').values_list('user__id',
                                                                                             'user__first_name',
                                                                                             'user__last_name')
    context['events'] = Event.objects.filter(
        belongs_to__userprofile__organization=request.user.userprofile.organization)
    return render(request, 'dashboard/index.html', context)


@login_required()
def swap_page(request):
    context = {}
    events = Event.objects.filter(belongs_to__userprofile__organization=request.user.userprofile.organization)
    if request.user.userprofile.is_admin:
        context['agreed_swaps'] = events.filter(~Q(agreed_swap=None))
        return render(request, 'dashboard/swap_admin.html', context)
    else:
        my_shifts = events.filter(belongs_to=request.user)
        context['my_shifts'] = my_shifts
        context['my_swaps'] = my_shifts.filter(requested_swap=True)
        context['my_transfers'] = my_shifts.filter(requested_transfer=True)
        context['other_swaps'] = events.filter(~Q(belongs_to=request.user)).filter(requested_swap=True)
        context['other_transfers'] = events.filter(~Q(belongs_to=request.user)).filter(requested_transfer=True)
        return render(request, 'dashboard/swap.html', context)


@csrf_exempt
def create_event(request):
    if request.method == "POST":
        if 'id' not in request.POST or ('id' in request.POST and request.POST['id'].strip() == ''):
            event_text = request.POST['text']
            start_date = request.POST['start_date']
            end_date = request.POST['end_date']
            user_id = request.POST['user']
            event = Event.objects.create(event_text=event_text, belongs_to=User.objects.get(pk=user_id),
                                         start_date=start_date, end_date=end_date)
        else:
            event = Event.objects.get(pk=request.POST['is'])
            event.event_text = request.POST['title']
            event.start_date = request.POST['start_date']
            event.end_date = request.POST['end_date']
            event.belongs_to = User.objects.get(pk=request.POST['user'])
            event.save()
        return HttpResponse(
            json.dumps({'id': event.id, 'title': event.event_text + ' - ' + event.belongs_to.get_full_name(),
                        'start': event.start_date, 'end': event.end_date}),
            content_type='application/json')
    return HttpResponse()


@csrf_exempt
def to_swap(request):
    if request.method == "POST":
        event_id = request.POST['id']
        e = Event.objects.get(pk=event_id)
        e.requested_swap = not e.requested_swap
        e.save()
    return HttpResponse()


@csrf_exempt
def pick_swap(request):
    if request.method == "POST":
        event_id = request.POST['id']
        e = Event.objects.get(pk=event_id)
        to_event_id = request.POST['to_id']
        to_event = Event.objects.get(pk=to_event_id)
        e.to_swap_events.add(to_event)
        e.save()
    return HttpResponse()


@csrf_exempt
def agree_swap(request):
    if request.method == "POST":
        event_id = request.POST['id']
        e = Event.objects.get(pk=event_id)
        to_event_id = request.POST['to_id']
        to_event = Event.objects.get(pk=to_event_id)
        e.agreed_swap = to_event
        e.save()
    return HttpResponse()


@csrf_exempt
def cancel_swap(request):
    if request.method == "POST":
        event_id = request.POST['id']
        e = Event.objects.get(pk=event_id)
        e.agreed_swap = None
        e.save()
    return HttpResponse()


@csrf_exempt
def approve_swap(request):
    if request.method == "POST":
        event_id = request.POST['id']
        e = Event.objects.get(pk=event_id)
        to_e = e.agreed_swap
        e.belongs_to, to_e.belongs_to = to_e.belongs_to, e.belongs_to
        e.agreed_swap = None
        to_e.agreed_swap = None
        e.requested_swap = False
        to_e.requested_swap = False
        e.requested_transfer = False
        to_e.requested_transfer = False
        e.to_swap_events = set()
        to_e.to_swap_events = set()
        to_e.save()
        e.save()
    return HttpResponse()