from datetime import date, datetime, timedelta
import json
from time import strptime

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import DataError, IntegrityError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import xlrd

from models import UserProfile, Event, legend_hr, PreviousTransfers


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
            messages.error(request, 'Incorrect Username/Password')
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
        if username == '' or password == '' or first_name == '' or last_name == '':
            messages.error(request, 'Please fill out all the credentials correctly')
            return redirect(reverse('dashboard:signup'))
        try:
            user = User.objects.create(username=username, email=username, first_name=first_name, last_name=last_name)
            UserProfile.objects.create(user=user, organization=organization, qualification=qualification)
        except (DataError, IntegrityError):
            messages.error(request, 'Please fill out all the credentials correctly')
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
    context['now'] = datetime.today().month
    return render(request, 'dashboard/index.html', context)


@login_required()
def organization_shifts(request):
    context = {'organization': True}
    return render(request, 'dashboard/index.html', context)


@login_required()
def swap_page(request):
    context = {}
    events = Event.objects.filter(belongs_to__userprofile__organization=request.user.userprofile.organization)
    if request.user.userprofile.is_admin:
        potential_agreed_swaps = list(events.filter(~Q(agreed_swap=None)).filter(requested_swap=True))
        agreed_swaps = set()
        for s in potential_agreed_swaps:
            if s.id not in agreed_swaps and s.agreed_swap.id not in agreed_swaps:
                agreed_swaps.add(s.id)
        context['agreed_swaps'] = Event.objects.filter(pk__in=list(agreed_swaps))
        context['agreed_transfers'] = events.filter(requested_transfer=True).filter(~Q(to_change_user=None))
        return render(request, 'dashboard/swap_admin.html', context)
    else:
        my_shifts = events.filter(belongs_to=request.user)
        context['my_shifts'] = my_shifts
        context['my_swaps'] = my_shifts.filter(requested_swap=True)
        context['my_transfers'] = my_shifts.filter(requested_transfer=True)
        context['other_swaps'] = events.filter(~Q(belongs_to=request.user)).filter(requested_swap=True)
        context['other_transfers'] = events.filter(~Q(belongs_to=request.user)).filter(requested_transfer=True)
        return render(request, 'dashboard/swap.html', context)


@login_required()
def previous_swap_page(request):
    context = {}
    if request.user.userprofile.is_admin:
        context['previous_swaps'] = PreviousTransfers.objects.filter(
            event__belongs_to__userprofile__organization=request.user.userprofile.organization)
        return render(request, 'dashboard/previous_swap_admin.html', context)


@login_required()
def get_shifts(request):
    type_shift = request.GET['type']
    start = request.GET['start']
    end = request.GET['end']
    if type_shift == 'admin':
        shifts = Event.objects.filter(belongs_to__userprofile__organization=request.user.userprofile.organization,
                                      start_date__range=(start, end))
    else:
        shifts = Event.objects.filter(belongs_to=request.user,
                                      belongs_to__userprofile__organization=request.user.userprofile.organization,
                                      start_date__range=(start, end))
    shifts = [x.json() for x in shifts]
    return HttpResponse(json.dumps(shifts), content_type='application/json')


@login_required()
def see_posted_shifts(request):
    context = {}
    swap_shifts = Event.objects.filter(~Q(belongs_to=request.user)).filter(
        belongs_to__userprofile__organization=request.user.userprofile.organization, requested_swap=True)
    transfer_shifts = Event.objects.filter(~Q(belongs_to=request.user)).filter(
        belongs_to__userprofile__organization=request.user.userprofile.organization, requested_transfer=True)
    context['events'] = (swap_shifts | transfer_shifts).distinct()
    context['events'] = [e for e in context['events'] if e.transfer_check or e.requested_swap]
    my_shifts = Event.objects.filter(belongs_to__userprofile__organization=request.user.userprofile.organization,
                                     belongs_to=request.user)
    context['my_shifts'] = my_shifts
    context['now'] = datetime.today().month
    return render(request, 'dashboard/index.html', context)


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
            event = Event.objects.get(pk=request.POST['id'])
            event.event_text = request.POST['text']
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
        to_event.requested_swap = True
        to_event.to_swap_events.add(e)
        to_event.save()
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
        if e.requested_swap:
            to_event.agreed_swap = e
            to_event.save()
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
def reject_swap(request):
    if request.method == "POST":
        event_id = request.POST['id']
        e = Event.objects.get(pk=event_id)
        to_event_id = request.POST['to_id']
        to_event = Event.objects.get(pk=to_event_id)
        if to_event in e.to_swap_events.all():
            e.to_swap_events.remove(to_event)
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
        PreviousTransfers.objects.create(from_user=e.belongs_to, to_user=to_e.belongs_to, event=e)
        PreviousTransfers.objects.create(from_user=to_e.belongs_to, to_user=e.belongs_to, event=e)
    return HttpResponse()


@csrf_exempt
def to_transfer(request):
    if request.method == "POST":
        event_id = request.POST['id']
        e = Event.objects.get(pk=event_id)
        e.requested_transfer = not e.requested_transfer
        e.to_change_user = None
        e.save()
    return HttpResponse()


@csrf_exempt
def pick_transfer(request):
    if request.method == "POST":
        event_id = request.POST['id']
        e = Event.objects.get(pk=event_id)
        e.to_change_user = request.user
        e.save()
    return HttpResponse()


@csrf_exempt
def cancel_transfer(request):
    if request.method == "POST":
        event_id = request.POST['id']
        e = Event.objects.get(pk=event_id)
        e.to_change_user = None
        if e.belongs_to == request.user:
            e.requested_transfer = False
        e.save()
    return HttpResponse()


@csrf_exempt
def approve_transfer(request):
    if request.method == "POST":
        event_id = request.POST['id']
        e = Event.objects.get(pk=event_id)
        new_belongs_to = e.to_change_user
        prev_belong = e.belongs_to
        e.belongs_to = new_belongs_to
        e.requested_transfer = False
        e.to_change_user = None
        e.save()
        PreviousTransfers.objects.create(from_user=prev_belong, to_user=e.belongs_to, event=e)
    return HttpResponse()


@login_required()
@csrf_exempt
def import_events(request):
    if request.method == "POST":
        f = request.FILES['file']
        add_events_from(f.read())
    return redirect(reverse('dashboard:main'))


def add_events_from(f):
    events = xlrd.open_workbook(file_contents=f)
    sheet = events.sheet_by_index(0)
    employees = []
    for i, item in enumerate(sheet.col(1)):
        if i < 6:
            continue
        elif item.value.strip() != '':
            print item.value
            # name = item.value.split(',')
            # try:
            # u = User.objects.get(first_name=name[1], last_name=name[0])
            # except User.DoesNotExist:
            # pass
            try:
                u = User.objects.get(username='employee' + str(i - 5) + '@employee.com')
            except User.DoesNotExist:
                u = User.objects.create(first_name='Employee', last_name=str(i - 5),
                                        email='employee' + str(i - 5) + '@employee.com',
                                        username='employee' + str(i - 5) + '@employee.com')
                UserProfile.objects.create(user=u, organization='UHN', qualification='RN')
                u.set_password('employee' + str(i - 5))
                u.save()
            employees.append(u)
    year = sheet.cell_value(1, 1)
    start_date = sheet.cell_value(4, 2)
    start_month = sheet.cell_value(2, 5)
    cur_date = date(int(year), strptime(start_month, '%b').tm_mon, int(start_date))
    cur_num = 2
    all_blank = False
    k = 0
    while not all_blank:
        if k > 100000:
            break
        else:
            print "Current Date", str(cur_date)
            try:
                if str(sheet.cell_value(4, cur_num)).strip() != '':
                    for i, e in enumerate(employees):
                        cell_val = str(sheet.cell_value(i + 6, cur_num))
                        print cell_val
                        if cell_val.strip() != '':
                            if cell_val in legend_hr:
                                t = legend_hr[cell_val]
                                event_times = [datetime.combine(cur_date, t[0])]
                                if t[1] < t[0]:
                                    start_date_temp = cur_date + timedelta(days=1)
                                    event_times.append(datetime.combine(start_date_temp, t[1]))
                                else:
                                    event_times.append(datetime.combine(cur_date, t[1]))
                                event = Event.objects.create(belongs_to=e, event_text=cell_val,
                                                             start_date=event_times[0],
                                                             end_date=event_times[1])
                                print "Event Created", e.get_full_name(), event.start_date, event.end_date
                            all_blank = False
                    cur_date += timedelta(days=1)
                    cur_num += 1
                else:
                    break
            except Exception as e:
                print e
                break