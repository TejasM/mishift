from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Event(models.Model):
    belongs_to = models.ForeignKey(User, related_name='my_events')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=timezone.now)
    event_text = models.TextField(default='')

    requested_swap = models.BooleanField(default=False)
    agreed_swap = models.ForeignKey('Event', related_name='to_swap_agree', default=None, null=True, blank=True)
    approved_swap = models.BooleanField(default=False)

    requested_transfer = models.BooleanField(default=False)
    approved_transfer = models.BooleanField(default=False)

    to_swap_events = models.ManyToManyField('Event', default=None, null=True, blank=True)
    to_change_user = models.ForeignKey(User, related_name='transfer_events', default=None, null=True, blank=True)

    @property
    def transfer_check(self):
        return self.requested_transfer and not self.to_change_user


class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True)
    role = models.CharField(max_length=140, default='employee')
    qualification = models.CharField(max_length=140, default='RN')
    organization = models.CharField(max_length=140, default='UHN')

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __unicode__(self):
        return u'Profile of user: %s' % self.user.username


legend = {}