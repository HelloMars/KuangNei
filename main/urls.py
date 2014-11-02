from django.conf.urls import patterns, url
from main import views


urlpatterns = patterns(
    '',
    # post
    url(r'^post/$', views.dopost, name='post'),
    url(r'^channellist/$', views.channellist, name='channellist'),
    url(r'^postlist/$', views.postlist, name='postlist'),

    # qiniu
    url(r'^getUpToken/$', views.get_uptoken, name='getUpToken'),
    url(r'^getDnUrl/$', views.get_dnurl, name='getDnUrl'),

    # user system
    url(r'^checkIfUserExist/$', views.check_if_user_exist, name='checkIfExist'),
    url(r'^signin/$', views.login_in, name='login'),
    url(r'^logout/$', views.logout_out, name='logout'),
    url(r'^register/$', views.register, name='regist'),
    url(r'^addUserInfo/$', views.add_user_info, name='addUserInfo'),
    url(r'^reply/$', views.reply_post, name='replyPost'),
    url(r'^uppost/$', views.up_post, name='uppost'),
    url(r'^opposepost/$', views.oppose_post, name='opposePost'),
    url(r'^upreply/$', views.up_reply, name='upReply'),
    url(r'^replyList/$', views.reply_list, name='replyList'),
    url(r'^myPost/$', views.my_post, name='myPost'),
    url(r'^replyInfo/$', views.reply_info, name='myReply'),
    url(r'^checkVersion/$', views.check_version, name='checkVersion'),
    url(r'^feedBack/$', views.feed_back, name='feedBack'),
    url(r'^addSchool/$', views.add_school_info, name='addSchool'),
    url(r'^hasUnreadMessage/$', views.if_has_unread_message, name='hasUnreadMessage'),

    url(r'^redis/$', views.redis, name='redis'),

    url(r'^edit.html$', views.some_view),
)
