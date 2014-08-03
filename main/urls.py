from django.conf.urls import patterns, url

from main import views

urlpatterns = patterns('',
    url(r'^category/$', views.category, name='category'),
    url(r'^postlist/$', views.postlist, name='postlist'),
    url(r'^pushMessageToApp/$', views.pushMessageToApp, name='pushMessageToApp'),
)
