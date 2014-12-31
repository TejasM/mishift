from django.contrib.auth import logout
from django.shortcuts import redirect

__author__ = 'tmehta'


def logout_user(request):
    logout(request)
    return redirect('/')