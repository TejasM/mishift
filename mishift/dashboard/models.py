from datetime import time
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Event(models.Model):
    belongs_to = models.ForeignKey(User, related_name='my_events', null=True, blank=True, default=None)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)
    event_text = models.TextField(default='')

    requested_swap = models.BooleanField(default=False)
    agreed_swap = models.ForeignKey('Event', related_name='to_swap_agree', default=None, null=True, blank=True)
    approved_swap = models.BooleanField(default=False)

    swap_request_time = models.DateTimeField(default=None, null=True, blank=True)
    transfer_request_time = models.DateTimeField(default=None, null=True, blank=True)

    requested_transfer = models.BooleanField(default=False)
    approved_transfer = models.BooleanField(default=False)

    to_swap_events = models.ManyToManyField('Event', default=None, null=True, blank=True)
    to_transfer_events = models.ManyToManyField(User, related_name='to_pickup_events', default=None, null=True,
                                                blank=True)
    to_change_user = models.ForeignKey(User, related_name='transfer_events', default=None, null=True, blank=True)

    def __unicode__(self):
        return self.event_text + ' - ' + self.belongs_to.get_full_name()

    @property
    def transfer_check(self):
        return self.requested_transfer

    def json(self):
        return {
            'id': self.id,
            'title': str(self.event_text + " for " + self.belongs_to.get_full_name()),
            'start': self.start_date.strftime('%Y-%m-%dT%X-05:00'),
            'end': self.end_date.strftime('%Y-%m-%dT%X-05:00'),
            'user_id': self.belongs_to.id,
            'to_swap': self.requested_swap,
            'to_transfer': self.requested_transfer,
        }


class PreviousTransfers(models.Model):
    from_user = models.ForeignKey(User, related_name='from_prev_transfer')
    to_user = models.ForeignKey(User, related_name='to_prev_transfer')
    event = models.ForeignKey(Event)
    approve_time = models.DateTimeField(default=timezone.now)


class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True)
    role = models.CharField(max_length=140, default='employee')
    qualification = models.CharField(max_length=140, default='RN')
    organization = models.CharField(max_length=140, default='UHN')
    first_time = models.BooleanField(default=True)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __unicode__(self):
        return u'Profile of user: %s' % self.user.username


legend_hr = {'TD': (time(hour=11, minute=0, second=0, microsecond=0), time(hour=23, minute=0, second=0, microsecond=0)),
             'TN': (time(hour=19, minute=0, second=0, microsecond=0), time(hour=9, minute=0, second=0, microsecond=0)),
             'TE': (time(hour=12, minute=0, second=0, microsecond=0), time(hour=21, minute=0, second=0, microsecond=0)),
             'D': (time(hour=7, minute=0, second=0, microsecond=0), time(hour=19, minute=0, second=0, microsecond=0)),
             'N': (time(hour=19, minute=0, second=0, microsecond=0), time(hour=7, minute=0, second=0, microsecond=0))}