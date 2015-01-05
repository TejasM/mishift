from dashboard import views
from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'^login/$', views.login_user, name='login'),
                       url(r'^sign_up/$', views.sign_up, name='signup'),
                       url(r'^main/$', views.main, name='main'),
                       url(r'^posted_shifts/$', views.see_posted_shifts, name='posted_shifts'),
                       url(r'^swap/$', views.swap_page, name='swap_page'),

                       url(r'^create_event/$', views.create_event, name='event'),

                       url(r'^to_swap/$', views.to_swap, name='to_swap'),
                       url(r'^pick_swap/$', views.pick_swap, name='pick_swap'),
                       url(r'^cancel_swap/$', views.cancel_swap, name='cancel_swap'),
                       url(r'^agree_swap/$', views.agree_swap, name='agree_swap'),
                       url(r'^approve_swap/$', views.approve_swap, name='approve_swap'),

                       url(r'^to_transfer/$', views.to_transfer, name='to_transfer'),
                       url(r'^pick_transfer/$', views.pick_transfer, name='pick_transfer'),
                       url(r'^cancel_transfer/$', views.cancel_transfer, name='cancel_transfer'),
                       url(r'^approve_transfer/$', views.approve_transfer, name='approve_transfer'),
)