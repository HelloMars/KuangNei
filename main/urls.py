from django.conf.urls import patterns, url

from main import views

urlpatterns = patterns('',
	url(r'^post/$', views.post, name='post'),
    url(r'^channellist/$', views.channellist, name='channellist'),
    url(r'^postlist/$', views.postlist, name='postlist'),
    url(r'^pushMessageToApp/$', views.pushMessageToApp, name='pushMessageToApp'),
)
