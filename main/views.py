#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
import random

from django.contrib.auth import authenticate, logout, login, SESSION_KEY
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction, connection
from django.db.models import F, Q
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import redirect, render_to_response
from django.core.cache import cache
import time

from kuangnei import consts
from kuangnei.utils import logger
from main.models import *
import post_push
from django.contrib.auth.models import Permission
from django.contrib.auth.hashers import make_password, check_password
# Create your views here.


@login_required
def get_uptoken(request):
    uptoken = utils.get_uptoken(consts.QINIU_SCOP)
    ret = utils.wrap_message({'uptoken': uptoken})
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
def get_dnurl(request):
    key = request.GET.get("key")
    if key is None:
        ret = utils.wrap_message(code=1)
    else:
        dnurl = utils.get_dnurl(key)
        ret = utils.wrap_message({'dnurl': dnurl})
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
@permission_required('kuangnei.'+consts.FORBIDDEN_AUTH, raise_exception=True)
def do_post(request):
    if request.method != 'POST':
        ret = utils.wrap_message(code=2)
    else:
        userid = request.session[SESSION_KEY]
        channelid = 1
        content = request.POST.get("content")
        imageurl = request.POST.get("imageurl")
        if channelid is None or content is None:
            ret = utils.wrap_message(code=1)
        elif int(channelid) == consts.NEWEST_CHANNEL_ID or int(channelid) == consts.HOTTEST_CHANNEL_ID:
            ret = utils.wrap_message(code=20, msg="最新/最热频道不允许发帖")
        else:
            user_post_count = UserAction.objects.filter(userId=userid, type=2,
                                                           actionTime__startswith=time.strftime('%Y-%m-%d'))
            if user_post_count.count() >= consts.POST_COUNT_LIMIT:                         #每天上限三次发帖
                ret = utils.wrap_message(code=3, msg="今天发帖次数已达上限")
            else:
                action_time = time.strftime('%Y-%m-%d %H:%M:%S')
                UserAction.objects.create(userId=userid, type=2, actionTime=action_time)     #统计代码
                user = User.objects.get(id=userid)
                school_id = UserInfo.objects.get(user=user).schoolId
                post = Post(user=user, schoolId=school_id, content=content, channelId=channelid,
                            opposedCount=0, postTime=time.strftime('%Y-%m-%d %H:%M:%S'),
                            replyCount=0, replyUserCount=0, imageUrls=imageurl,
                            score=utils.cal_post_score(0, 0, 0, time.time()),
                            editStatus=0, upCount=0)
                post.save()
                logger.info("post " + str(post.id))
                #_push_message_to_app(post.content)
                ret = utils.wrap_message({'postId': post.id})
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
def postlist(request):
    userid = request.session[SESSION_KEY]
    channelid = request.GET.get("channelid")
    page = request.GET.get("page")
    if channelid is None or page is None:
        ret = utils.wrap_message(code=1)
    else:
        action_time = time.strftime('%Y-%m-%d %H:%M:%S')
        UserAction.objects.create(userId=userid, type=1, actionTime=action_time)
        page = int(page)
        start = (page - 1) * consts.POST_LOAD_SIZE
        end = start + consts.POST_LOAD_SIZE
        school_info = SchoolInfo.objects.filter(userinfo__user=userid)[0]
        if int(channelid) == consts.NEWEST_CHANNEL_ID:  # 获取区域最新帖子列表
            posts = Post.objects.filter(schoolId=school_info.id).order_by("-postTime")[start:end]
            logger.info("newest postlist %d:[%d, %d]", len(posts), start, end)
        elif int(channelid) == consts.HOTTEST_CHANNEL_ID:  # 获取区域最热帖子列表
            posts = Post.objects.filter(schoolId=school_info.id).order_by("-score")[start:end]
            logger.info("hottest postlist %d:[%d, %d]", len(posts), start, end)
        else:  # 获取频道帖子列表
            posts = Post.objects.filter(channelId=channelid, schoolId=school_info.id).order_by("-postTime")[start:end]
            logger.info("channel postlist %d:[%d, %d]", len(posts), start, end)
        ret = utils.wrap_message({'size': len(posts)})
        ret['school'] = school_info.to_json()
        ret['list'] = [e.tojson(_fill_user_info(e.user)) for e in posts]
    return HttpResponse(json.dumps(ret, default=utils.datetimeHandler),
                        mimetype='application/json')


def register(request):
    if request.method != 'POST':
        ret = utils.wrap_message(code=2)
    else:
        token = request.POST.get('token')
        logger.info('aaaaaa')
        logger.info(token)
        old_user_info_list = UserInfo.objects.filter(toke=token)
        if old_user_info_list.count() != 0:              #证明该用户之前已经注册过
            logger.info('查询了查询了')
            old_user_info = old_user_info_list[0]
            old_user = User.objects.get(id=old_user_info.user.id)
            old_password = make_password(old_user.username, 'kuangnei', 'pbkdf2_sha256')
            user = authenticate(username=old_user.username, password=old_password)
            login(request, user)
            permission = Permission.objects.get(codename=consts.FORBIDDEN_AUTH)
            user.user_permissions.add(permission)
            request.session.set_expiry(3000000000)  # session永不失效
            logger.info('老用户重新注册成功')
            ret = utils.wrap_message({'user': old_user.username, 'password': old_password})
        else:
            school_id = request.POST.get("schoolId")
            school_info = utils.get(SchoolInfo, id=school_id)
            if school_id is None or school_info is None:
                ret = utils.wrap_message(code=1)
            else:
                with transaction.atomic():
                    UserId.objects.filter(id=1).update(currentId=F('currentId')+1)
                    user_id = UserId.objects.get(id=1)
                    username = user_id.currentId
                    password = make_password(username, 'kuangnei', 'pbkdf2_sha256')
                    user = User.objects.create_user(username=username, password=password)
                if user is None:
                        ret = utils.wrap_message(code=10, msg='注册失败')
                        logger.warn('注册失败')
                else:
                    try:
                        # 在user_info表中设置token, nickname, telephone
                        user_info = UserInfo.objects.create(user=user, schoolId=school_info,
                                                token=token)
                        user = authenticate(username=username, password=password)
                        login(request, user)
                        permission = Permission.objects.get(codename=consts.FORBIDDEN_AUTH)
                        user.user_permissions.add(permission)
                        request.session.set_expiry(3000000000)  # session永不失效
                        ret = utils.wrap_message({'user': user.username, 'password': password})
                        logger.info('注册新用户(%s)成功', repr(user))
                    except Exception as e:
                        logger.exception(e)
                        user.delete()
                        user_info.delete()
    return HttpResponse(json.dumps(ret, ensure_ascii=False))


#检查用户名是否已经存在
def check_if_user_exist(request):
    if request.method != 'POST':
        ret = utils.wrap_message(code=2)
    else:
        username = request.POST.get('username')
        user = User.objects.filter(username=username)
        if user:
            ret = utils.wrap_message({'exist': True})
        else:
            ret = utils.wrap_message({'exist': False})
    return HttpResponse(json.dumps(ret, ensure_ascii=False))


def _login(data, request):
    username = data.get('username')
    password = data.get('password')
    if username is None or password is None:
        ret = utils.wrap_message(code=1)
    else:
        user = authenticate(username=username, password=password)
        if user is None:
            ret = utils.wrap_message(code=10, msg='用户名或密码错误')
            logger.info('用户名或密码错误')
        else:
            if user.is_active:
                login(request, user)
                user_info = UserInfo.objects.get(user=user)
                modify = user_info.setattrs(data)
                if modify:
                    user_info.save()
                    logger.info('修改用户(%s)信息成功', repr(user.id))
                request.session.set_expiry(30000000)
                ret = utils.wrap_message(data=user_info.tojson, code=0, msg='登陆成功')
            else:
                ret = utils.wrap_message(code=10, msg='用户无权限')
                logger.info('用户无权限')
    return ret


# http://kuangnei.me/zhumeng/accounts/login/?
# next=/zhumeng/kuangnei/api/channellist/&username=18910690027&password=~%21%40%23%60123qwer&deviceid=xxx
def rlogin_in(request):
    username = request.GET.get('username')
    password = request.GET.get('password')
    if username is None or password is None:
        raise Http404
    else:
        _login(request.GET, request)
        return redirect(request.GET.get('next'))


def login_in(request):
    if request.method != 'POST':
        ret = utils.wrap_message(code=2)
    else:
        ret = _login(request.POST, request)
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
def logout_out(request):
    logout(request)
    ret = utils.wrap_message(code=0, msg='退出成功')
    return HttpResponse(json.dumps(ret), mimetype='application/json')


#修改用户信息
@login_required
def add_user_info(request):
    if request.method != 'POST':
        ret = utils.wrap_message(code=2)
    else:
        userid = request.session[SESSION_KEY]
        action_time = time.strftime('%Y-%m-%d %H:%M:%S')
        UserAction.objects.create(userId=userid, type=4, actionTime=action_time)     #统计代码
        user_info = UserInfo.objects.get(user=userid)
        modify = user_info.setattrs(request.POST)
        user_name = _has_other_used(user_info.user, user_info.nickname)
        if user_name is None:                #没有其他人用过
            UsedName.objects.create(user=user_info.user, name=user_info.nickname)
            try:
                if modify:
                    user_info.save()
                    ret = utils.wrap_message(data=user_info.tojson, msg='修改个人信息成功')
                    logger.info('修改用户(%s)信息成功', repr(userid))
                else:
                    ret = utils.wrap_message(data=user_info.tojson, msg='获取个人信息成功')
            except Exception as e:
                logger.exception(e)
                ret = utils.wrap_message(code=2)
        else:
            ret = utils.wrap_message(code=1, msg='该用户名已被其他用户使用过')
    return HttpResponse(json.dumps(ret, default=utils.dateHandler), mimetype='application/json')


@login_required
def channellist(request):
    foos = {
        'returnCode': 0,
        'returnMessage': '',
        'size': 6,
        'list': [
            {'id': consts.NEWEST_CHANNEL_ID, 'title': '最新'},
            {'id': consts.HOTTEST_CHANNEL_ID, 'title': '最热'},
            {'id': 1, 'title': '有趣', 'subtitle': '你认为有趣的东西'},
            {'id': 2, 'title': '匿名', 'subtitle': '请不要用文字伤害他人'},
            {'id': 11, 'title': '娱乐', 'subtitle': '电影、电视、音乐、旅游'},
            {'id': 12, 'title': '男女', 'subtitle': '关于男生女生之间的事'}
        ]
    }
    data = json.dumps(foos)
    return HttpResponse(data, mimetype='application/json')


def _up_oppose_post(request, model, key):
    postid = request.POST.get('postId')
    post = utils.get(Post, id=postid)  # 验证postid有效性
    if postid is None or post is None:
        ret = utils.wrap_message(code=1)
    else:
        userid = request.session[SESSION_KEY]
        if post.user.id == userid:  # 自己赞（踩）
            ret = utils.wrap_message(code=5, data={key: getattr(post, key)}, msg="嘿嘿")
        else:  # 他人赞（踩）
            upoppose = utils.get(model, postId=postid, userId=userid)
            if upoppose is None:  # 用户未赞（踩）过
                model.objects.create(postId=postid, userId=userid)
                message = "赞（踩）成功"
                addend = 1
                action = 'do'
            else:  # 用户已经赞（踩）过则取消之前的赞（踩）
                upoppose.delete()
                message = "取消赞（踩）成功"
                addend = -1
                action = 'cancel'
            with transaction.atomic():
                Post.objects.filter(id=postid).update(**{key: F(key)+addend})
                _update_post_score(postid)
            ret = utils.wrap_message(code=0, data={key: getattr(post, key)+addend}, msg=message)
            ret['action'] = action
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
@permission_required('kuangnei.'+consts.FORBIDDEN_AUTH, raise_exception=True)
def up_post(request):
    return _up_oppose_post(request, UpPost, 'upCount')


@login_required
@permission_required('kuangnei.'+consts.FORBIDDEN_AUTH, raise_exception=True)
def oppose_post(request):
    return _up_oppose_post(request, OpposePost, 'opposedCount')


@login_required
@permission_required('kuangnei.'+consts.FORBIDDEN_AUTH, raise_exception=True)
def up_reply(request):
    reply_id = request.POST.get('ReplyId')
    reply = utils.get(Reply, id=reply_id)  # 验证reply_id有效性
    user_id = request.session[SESSION_KEY]
    if reply_id is None or reply is None:
        ret = utils.wrap_message(code=1)
    else:
        if reply.fromUser.id == user_id:  # 自己赞
            ret = utils.wrap_message(code=20, data={'upCount': reply.upCount}, msg="自己赞无效")
        else:
            up_reply = utils.get(UpReply, ReplyId=reply_id, userId=user_id)
            if up_reply is None:  # 用户未赞过
                UpReply.objects.create(postId=reply.post.id, replyId=reply_id, userId=user_id)
                message = "赞成功"
                addend = 1
                action = 'do'
            else:  # 用户已经赞过则取消之前的赞
                up_reply.delete()
                message = "取消赞成功"
                addend = -1
                action = 'cancel'
            Reply.objects.filter(id=reply_id).update(upCount=F('upCount')+addend)
            ret = utils.wrap_message(code=0, data={'upCount': reply.upCount+addend}, msg=message)
            ret['action'] = action
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
@permission_required('kuangnei.'+consts.FORBIDDEN_AUTH, raise_exception=True)
def reply_post(request):
    from_user_id = request.session[SESSION_KEY]
    to_user_id = request.POST.get('toUserId')
    post_id = request.POST.get('postId')
    content = request.POST.get('content')
    post = utils.get(Post, id=post_id)  # 验证post_id有效性
     #验证user有效性
    from_user = utils.get(User, id=from_user_id)
    to_user = utils.get(User, id=to_user_id)
    if post_id is None or content is None or from_user_id is None or post is None or to_user_id is None\
            or from_user is None or to_user is None:
        ret = utils.wrap_message(code=1)
    else:
        reply_time = time.strftime('%Y-%m-%d %H:%M:%S')
        UserAction.objects.create(userId=from_user_id, type=3, actionTime=reply_time)     #统计代码
        with transaction.atomic():                                                  # 确保原子操作
            Post.objects.filter(id=post_id).update(replyCount=F('replyCount')+1)  # 总回复数+1
            reply = Reply.objects.create(post=post, fromUser=from_user, toUser=to_user, upCount=0,
            content=content,  replyTime=reply_time, editStatus=0, hasRead=0)
        user_info = UserInfo.objects.get(user=to_user)                         #消息推送
        from_user_info = UserInfo.objects.get(user=from_user)
        token = user_info.token
        if token is not None:
            push_content = from_user_info.nickname + u'回复了你'
            _push_message_to_single(push_content, token)
        ret = utils.wrap_message(data={"ReplyId": reply.id}, code=0, msg="回复成功")
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
def reply_list(request):
    post_id = request.GET.get("postId")
    page = request.GET.get("page")
    post = utils.get(Post, id=post_id)
    if post_id is None or post is None or page is None:
        ret = utils.wrap_message(code=1)
    else:
        page = int(page)
        start = (page - 1) * consts.REPLY_LOAD_SIZE
        end = start + consts.REPLY_LOAD_SIZE
        replies = Reply.objects.filter(post=post).order_by("-replyTime")[start:end]
        logger.info("first_level_replies %d:[%d, %d]", replies.count(), start, end)
        ret = utils.wrap_message({'postId': int(post_id), 'size': replies.count()})
        ret['list'] = [e.to_json(_fill_user_info(e.fromUser), _fill_user_info(e.toUser)) for e in replies]
    return HttpResponse(json.dumps(ret, default=utils.datetimeHandler), mimetype='application/json')


#消息之我的帖子
@login_required
def my_post(request):
    user_id = request.session[SESSION_KEY]
    page = request.GET.get("page")
    user = utils.get(User, id=user_id)
    if user_id is None or page is None or user is None:
        ret = utils.wrap_message(code=1)
    else:
        page = int(page)
        start = (page - 1) * consts.POST_LOAD_SIZE
        end = start + consts.POST_LOAD_SIZE
        posts = Post.objects.filter(user=user).order_by("-postTime")[start:end]
        d = {}
        ret = utils.wrap_message({'size': posts.count()})
        #TODO:此处是我的帖子列表，是否需要把我的信息带上返回
        ret['list'] = [e.tojson(_fill_user_info(e.user)) for e in posts]
    return HttpResponse(json.dumps(ret, default=utils.datetimeHandler), mimetype='application/json')


#消息之回复
@login_required
def reply_info(request):
    user_id = request.session[SESSION_KEY]
    page = request.GET.get("page")
    user = utils.get(User, id=user_id)
    if user_id is None or page is None or user is None:
        ret = utils.wrap_message(code=1)
    else:
        page = int(page)
        start = (page - 1) * consts.REPLY_INFO_LOAD_SIZE
        end = start + consts.REPLY_INFO_LOAD_SIZE
        replies = Reply.objects.filter(Q(toUser=user_id) | Q(fromUser=user_id)).order_by("-replyTime")[start:end]
        Reply.objects.filter(toUser=user_id, hasRead=0).update(hasRead=1)
        ret = utils.wrap_message({'size': replies.count()})
        ret['list'] = [e.to_reply_json(_fill_user_info(e.fromUser), _fill_user_info(e.toUser),\
                        e.post.tojson(_fill_user_info(e.post.user))) for e in replies]
    return HttpResponse(json.dumps(ret, default=utils.datetimeHandler), mimetype='application/json')


@login_required
def if_has_unread_message(request):
    user_id = request.session[SESSION_KEY]
    if user_id is None:
        ret = utils.wrap_message(code=1)
    else:
        reply_info = Reply.objects.filter(toUser=user_id, hasRead=0)
        ret = utils.wrap_message({'unReadMessageCount': reply_info.count()})
    return HttpResponse(json.dumps(ret, default=utils.datetimeHandler), mimetype='application/json')

#意见反馈
@login_required
def feed_back(request):
    user_id = request.session[SESSION_KEY]
    content = request.POST.get("content")
    type = request.POST.get("type")
    try:
        user = utils.get(User, id=user_id)
        if user_id is None or content is None or user is None:
            ret = utils.wrap_message(code=1)
        else:
            FeedBack.objects.create(user=user, type=type, content=content)
            ret = utils.wrap_message()
    except Exception as e:
            logger.exception(e)
            ret = utils.wrap_message(code=20)
    return HttpResponse(json.dumps(ret, default=utils.datetimeHandler), mimetype='application/json')


def check_version(request):
    version = request.GET.get("version")
    if version is None:
        ret = utils.wrap_message(code=1)
    else:
        try:
            version_number = int(version)
            max_version = Version.objects.order_by("-versionNumber")[0]
            if max_version.versionNumber != version_number:                       #当前版本不是最新
                data = max_version.to_json()
                ret = utils.wrap_message(data=data, code=0, msg="有新版本")
            else:
                ret = utils.wrap_message(code=0, msg="没有新版本")
        except Exception as e:
            logger.exception(e)
            ret = utils.wrap_message(code=20)
    return HttpResponse(json.dumps(ret), mimetype='application/json')


def add_school_info(request):
    name = request.POST.get("name")
    area = request.POST.get("area")
    position = request.POST.get("position")
    if name == "" or area == "" or position == "":
        ret = utils.wrap_message(code=1)
    else:
        try:
            SchoolInfo.objects.create(name=name, area=area, position=position)
            ret = utils.wrap_message(code=0)
        except Exception as e:
            logger.exception(e)
            ret = utils.wrap_message(code=20)
    return HttpResponse(json.dumps(ret), mimetype='application/json')


def get_school_info(request):
    ret = utils.wrap_message(code=0)
    ret['list'] = [e.to_json2() for e in SchoolInfo.objects.raw('SELECT * FROM school_info')]
    return HttpResponse(json.dumps(ret), mimetype='application/json')


#漂流瓶
@login_required
def floater(request):
    user_id = request.session[SESSION_KEY]
    user = utils.get(User, id=user_id)
    content = request.POST.get('content')
    if user_id is None or user is None or content is None:
        ret = utils.wrap_message(code=1)
    else:
        user_floater_count = UserAction.objects.filter(userId=user_id, type=5,
                                                       actionTime__startswith=time.strftime('%Y-%m-%d'))
        if user_floater_count.count() >= consts.FLOATER_COUNT_LIMIT:                         #每天上限三次漂流瓶
            ret = utils.wrap_message(code=3, msg="今天发送漂流瓶的次数已达上限")
        else:
            action_time = time.strftime('%Y-%m-%d %H:%M:%S')
            user_info = UserInfo.objects.get(user=user_id)
            sex = user_info.sex
            if sex != 0 and sex != 1:
                ret = utils.wrap_message(code=4, msg="您的性别还未知，请完善个人信息")
            else:
                school_info = SchoolInfo.objects.filter(userinfo__user=user_id)[0]
                opposite_sex = UserInfo.objects.filter(schoolId=school_info.id, sex=sex ^ 1)   #该校异性
                opposite_sex_count = opposite_sex.count()
                if opposite_sex_count == 0:
                    ret = utils.wrap_message(code=5, msg="该校还没有异性，邀吗")
                else:
                    ran = random.randint(0, opposite_sex_count-1)
                    choiced_user_info = opposite_sex[ran]             #被选出来的人
                    choiced_user = User.objects.get(id=choiced_user_info.id)
                    with transaction.atomic():
                         #发表一条虚拟帖子
                        virtual_post = Post(user=choiced_user, schoolId=school_info, channelId=0, opposedCount=0, upCount=0,
                                    score=0, postTime=time.strftime('%Y-%m-%d %H:%M:%S'), replyCount=0, replyUserCount=0,
                                    editStatus=0)
                        virtual_post.save()
                        #当前人回复
                        reply = Reply(post=virtual_post, fromUser=user, toUser=choiced_user, upCount=0,
                        content=content,  replyTime=time.strftime('%Y-%m-%d %H:%M:%S'), editStatus=0, hasRead=0)
                        reply.save()
                    #推送给发虚拟帖子的人
                    token = choiced_user_info.token
                    if token is not None:
                        push_content = u'你收到了一个漂流瓶'
                        _push_message_to_single(push_content, token)
                    ret = utils.wrap_message(data={"ReplyId": reply.id}, code=0, msg="发送成功")
                    UserAction.objects.create(userId=user_id, type=5, actionTime=action_time)     #统计代码
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
def today_topic(request):
    topic_time = time.strftime('%Y-%m-%d')
    try:
        topic = Topic.objects.filter().order_by("topicTime")[0]
        ret = utils.wrap_message(data=topic.to_json(), code=0)
    except Exception as e:
        logger.exception(e)
        ret = utils.wrap_message(code=1)
    return HttpResponse(json.dumps(ret), mimetype='application/json')


def _push_message_to_app(content):
    logger.info("pushMessageToApp")
    post_push.pushMessageToApp(content)


def _push_message_to_single(content, client_id):
    logger.info("pushMessageToSingle")
    post_push.pushMessageToSingle(content,client_id)


def _fill_user_info(user):
    nickname = None
    avatar = None
    try:
        user_info = UserInfo.objects.get(user=user)
        nickname = user_info.nickname
        sex = user_info.sex
        avatar = user_info.avatar
    except UserInfo.DoesNotExist:
        logger.warn("User or Userinfo not found")
    jsond = {"id": user.id,
             "sex":sex,
             #"avatar": avatar,
             "name": nickname}
    return jsond


# 解禁用户
def unforbid_user(user):
    if user is not None:
        permission = Permission.objects.get(codename=consts.FORBIDDEN_AUTH)
        user.user_permissions.add(permission)


# 禁言用户
def forbid_user(user):
    if user is not None:
        permission = Permission.objects.get(codename=consts.FORBIDDEN_AUTH)
        user.user_permissions.remove(permission)


# 调用该方法的事务操作已更新
def _update_post_score(_id):
    post = utils.get(Post, id=_id)
    r = post.replyUserCount
    z = post.upCount
    c = post.opposedCount
    ti = calendar.timegm(post.postTime.timetuple())
    post.score = utils.cal_post_score(r, z, c, ti)
    post.save()
    if c-z >= consts.FORBIDDEN_THRESHOLD:
        forbid_user(utils.get(User, id=post.userId))


# def _update_reply_score(_id):
#     Reply.objects.filter(id=_id).update(score=F('upCount')+F('replyUserCount'))


def redis(request):
    cache.set('foo', 'value', timeout=25)
    logger.info("redis: " + cache.get('foo') + ", " + str(cache.ttl('foo')))
    ret = utils.wrap_message(code=0)
    return HttpResponse(json.dumps(ret), mimetype='application/json')


def _get_post(first_level_reply):
    post_id = first_level_reply.postId
    try:
        post = Post.objects.get(postId=post_id)
        return post
    except post.DoesNotExist:
        return None


def _cut_str(str, length=16):
    return str[0:length]


def some_view(request):
   return render_to_response('edit.html')


def _has_other_used(user_id, name):
    try:
        used_name = UsedName.objects.get(Q(name=name) & ~Q(user=user_id))
        return used_name
    except UsedName.DoesNotExist:
        return None
    except Exception as e:
        logger.exception(e)
        return 'error'
