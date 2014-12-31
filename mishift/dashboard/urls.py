from dashboard import views
from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'^login/$', views.login_user, name='login'),
                       url(r'^sign_up/$', views.sign_up, name='signup'),
                       url(r'^main/$', views.main, name='main'),
                       url(r'^swap/$', views.swap_page, name='swap_page'),

                       url(r'^create_event/$', views.create_event, name='event'),

                       url(r'^to_swap/$', views.to_swap, name='to_swap'),
                       url(r'^pick_swap/$', views.pick_swap, name='pick_swap'),
                       url(r'^cancel_swap/$', views.cancel_swap, name='cancel_swap'),
                       url(r'^agree_swap/$', views.agree_swap, name='agree_swap'),
                       url(r'^approve_swap/$', views.approve_swap, name='approve_swap'),
)