from django.conf.urls import patterns, url
from main import views


urlpatterns = patterns(
    '',
    url(r'^post/$', views.post, name='post'),
    url(r'^channellist/$', views.channellist, name='channellist'),
    url(r'^postlist/$', views.postlist, name='postlist'),
    url(r'^getUpToken/$', views.get_uptoken, name='getUpToken'),
    url(r'^getDnUrl/$', views.get_dnurl, name='getDnUrl'),
    url(r'^checkIfUserExist/$', views.check_if_user_exist, name='checkIfExist'),
    url(r'^signin/$', views.login_in, name='login'),
    url(r'^logout/$', views.logout_out, name='logout'),
    url(r'^testLogin/$', views.test_view, name='testLogin'),
    url(r'^register/$', views.register, name='regist'),
    url(r'^addUserInfo/$', views.add_user_info, name='addUserInfo'),
    url(r'^responsePost/$', views.response_post, name='responsePost')
)
