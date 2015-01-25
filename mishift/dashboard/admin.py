from django.contrib import admin
from models import UserProfile, PreviousTransfers, Event

__author__ = 'tmehta'


admin.site.register(UserProfile)
admin.site.register(Event)
admin.site.register(PreviousTransfers)