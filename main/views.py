#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
import time
import calendar

from django.contrib.auth import authenticate, logout, login, SESSION_KEY
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import redirect
from django.core.cache import cache

from kuangnei import consts
from kuangnei.utils import logger
from main.models import *
import post_push
from django.contrib.auth.models import Permission

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
def dopost(request):
    if request.method != 'POST':
        ret = utils.wrap_message(code=2)
    else:
        userid = request.session[SESSION_KEY]
        channelid = request.POST.get("channelid")
        content = request.POST.get("content")
        if channelid is None or content is None:
            ret = utils.wrap_message(code=1)
        elif int(channelid) == consts.NEWEST_CHANNEL_ID or int(channelid) == consts.HOTTEST_CHANNEL_ID:
            ret = utils.wrap_message(code=20, msg="最新/最热频道不允许发帖")
        else:
            post = Post(userId=userid, schoolId=1, content=content, channelId=channelid,
                        opposedCount=0, postTime=time.strftime('%Y-%m-%d %H:%M:%S'),
                        replyCount=0, replyUserCount=0,
                        score=utils.cal_post_score(0, 0, 0, time.time()),
                        editStatus=0, upCount=0)
            post.save()
            logger.info("post " + str(post.id))
            imageurl = request.POST.get("imageurl")
            if imageurl is not None:
                # TODO: 为什么不直接把imageurl存到数据库，取得时候再反序列化
                imageurls = imageurl.split("@")
                for url in imageurls:
                    post_picture = PostPicture(pictureUrl=url, postId=post.id)
                    post_picture.save()
                logger.info("save %d pictures", len(imageurls))
            _push_message_to_app(post)
            ret = utils.wrap_message({'postId': post.id})
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
def postlist(request):
    channelid = request.GET.get("channelid")
    page = request.GET.get("page")
    if channelid is None or page is None:
        ret = utils.wrap_message(code=1)
    else:
        page = int(page)
        start = (page - 1) * consts.LOAD_SIZE
        end = start + consts.LOAD_SIZE
        if int(channelid) == consts.NEWEST_CHANNEL_ID:  # 获取区域最新帖子列表
            posts = Post.objects.filter(schoolId=1).order_by("-postTime")[start:end]
            logger.info("newest postlist %d:[%d, %d]", len(posts), start, end)
        elif int(channelid) == consts.HOTTEST_CHANNEL_ID:  # 获取区域最热帖子列表
            posts = Post.objects.filter(schoolId=1).order_by("-score")[start:end]
            logger.info("hottest postlist %d:[%d, %d]", len(posts), start, end)
        else:  # 获取频道帖子列表
            posts = Post.objects.filter(channelId=channelid).order_by("-postTime")[start:end]
            logger.info("channel postlist %d:[%d, %d]", len(posts), start, end)
        d = {}
        for e in posts:
            pictures = PostPicture.objects.filter(postId=e.id).values_list("pictureUrl", flat=True)
            d[e.id] = list(pictures)
        ret = utils.wrap_message({'size': len(posts)})
        ret['list'] = [e.tojson(d[e.id], _fill_user_info(e.userId)) for e in posts]
    return HttpResponse(json.dumps(ret, default=utils.datetimeHandler),
                        mimetype='application/json')


def register(request):
    if request.method != 'POST':
        ret = utils.wrap_message(code=2)
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username is None or password is None:
            ret = utils.wrap_message(code=1)
        else:
            if not utils.is_avaliable_phone(username):
                ret = utils.wrap_message(code=11, msg='电话有误')
                return HttpResponse(json.dumps(ret, ensure_ascii=False))
            olduser = User.objects.filter(username=username).first()
            if olduser is None:
                newuser = User.objects.create_user(username=username, password=password)
                if newuser is None:
                    ret = utils.wrap_message(code=10, msg='注册失败')
                    logger.warn('注册失败')
                else:
                    # TODO: catch exception and delete user
                    # 在user_info表中设置token, nickname, telephone
                    deviceid = request.POST.get('deviceid')
                    token = request.POST.get('token')  # could be None
                    UserInfo.objects.create(userId=newuser.id, deviceId=deviceid,
                                            token=token, nickname='user'+str(newuser.id),
                                            telephone=username)
                    user = authenticate(username=username, password=password)
                    login(request, user)
                    permission = Permission.objects.get(codename=consts.FORBIDDEN_AUTH)
                    user.user_permissions.add(permission)
                    request.session.set_expiry(30000)  # session失效期5分钟
                    ret = utils.wrap_message({'user': newuser.username})
                    logger.info('注册新用户(%s)成功', repr(newuser))
            else:
                ret = utils.wrap_message(code=10, msg='用户名已存在')
                logger.info('用户名(%s)已存在', repr(olduser))
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
                user_info = UserInfo.objects.get(userId=user.id)
                modify = user_info.setattrs(data)
                if modify:
                    user_info.save()
                    logger.info('修改用户(%s)信息成功', repr(user.id))
                request.session.set_expiry(30000)
                ret = utils.wrap_message(code=0, msg='登陆成功')
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


@login_required
def add_user_info(request):
    if request.method != 'POST':
        ret = utils.wrap_message(code=2)
    else:
        userid = request.session[SESSION_KEY]
        user_info = UserInfo.objects.get(userId=userid)
        modify = user_info.setattrs(request.POST)

        if modify:
            user_info.save()
            ret = utils.wrap_message(data=user_info.tojson(), msg='修改个人信息成功')
            logger.info('修改用户(%s)信息成功', repr(userid))
        else:
            ret = utils.wrap_message(data=user_info.tojson(), msg='获取个人信息成功')
    # TODO: int return string bug
    return HttpResponse(json.dumps(ret, default=utils.dateHandler),
                        mimetype='application/json')


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
        if post.userId == userid:  # 自己赞（踩）
            ret = utils.wrap_message(code=20, data={key: getattr(post, key)}, msg="自己赞（踩）无效")
        else:  # 他人赞（踩）
            upoppose = utils.get(model, postId=postid)
            if upoppose is None:  # 用户未赞（踩）过
                model.objects.create(postId=postid, userId=userid)
                message = "赞（踩）成功"
                addend = 1
            else:  # 用户已经赞（踩）过则取消之前的赞（踩）
                upoppose.delete()
                message = "取消赞（踩）成功"
                addend = -1
            Post.objects.filter(id=postid).update(**{key: F(key)+addend})
            _update_post_score(postid)
            ret = utils.wrap_message(code=0, data={key: getattr(post, key)+addend}, msg=message)
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
    first_level_reply_id = request.POST.get('firstLevelReplyId')
    first_level_reply = utils.get(FirstLevelReply, id=first_level_reply_id)  # 验证first_level_reply_id有效性
    if first_level_reply_id is None or first_level_reply is None:
        ret = utils.wrap_message(code=1)
    else:
        userid = request.session[SESSION_KEY]
        if first_level_reply.userId == userid:  # 自己赞
            ret = utils.wrap_message(code=20, data={'upCount': first_level_reply.upCount}, msg="自己赞无效")
        else:  # 他人赞
            upreply = utils.get(UpReply, firstLevelReplyId=first_level_reply_id)
            if upreply is None:  # 用户未赞过
                UpReply.objects.create(postId=first_level_reply.postId,
                                       firstLevelReplyId=first_level_reply_id,
                                       userId=userid)
                message = "赞成功"
                addend = 1
            else:  # 用户已经赞过则取消之前的赞
                upreply.delete()
                message = "取消赞成功"
                addend = -1
            FirstLevelReply.objects.filter(id=first_level_reply_id).update(upCount=F('upCount')+addend)
            _update_reply_score(first_level_reply_id)
            ret = utils.wrap_message(code=0, data={'upCount': first_level_reply.upCount+addend}, msg=message)
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
@permission_required('kuangnei.'+consts.FORBIDDEN_AUTH, raise_exception=True)
def reply_first_level(request):
    userid = request.session[SESSION_KEY]
    postid = request.POST.get('postId')
    content = request.POST.get('content')
    post = utils.get(Post, id=postid)  # 验证postid有效性
    if postid is None or content is None or userid is None or post is None:
        ret = utils.wrap_message(code=1)
    else:
        reply_time = time.strftime('%Y-%m-%d %H:%M:%S')
        with transaction.atomic():
            Post.objects.filter(id=postid).update(replyCount=F('replyCount')+1)  # 总回复数+1
            first_level_reply = FirstLevelReply.objects.create(
                postId=postid, userId=userid, upCount=0,
                content=content, floor=Post.objects.get(id=postid).replyCount,  # 确保原子操作
                replyCount=0, replyUserCount=0, replyTime=reply_time,
                score=0, editStatus=0)
            if utils.get(ReplyPost, postId=postid) is None:  # 未回复过
                ReplyPost.objects.create(postId=postid, userId=userid)
                Post.objects.filter(id=postid).update(replyUserCount=F('replyUserCount')+1)  # 独立回复数+1
                _update_post_score(postid)
            ret = utils.wrap_message(data={"firstLevelReplyId": first_level_reply.id},
                                     code=0, msg="发表一级回复成功")
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
@permission_required('kuangnei.'+consts.FORBIDDEN_AUTH, raise_exception=True)
def reply_second_level(request):
    userid = request.session[SESSION_KEY]
    postid = request.POST.get('postId')
    first_level_reply_id = request.POST.get('firstLevelReplyId')
    content = request.POST.get('content')
    first_level_reply = utils.get(FirstLevelReply, id=first_level_reply_id)  # 验证first_level_reply_id有效性
    if postid is None or content is None or userid is None or first_level_reply_id is None or first_level_reply is None:
        ret = utils.wrap_message(code=1)
    else:
        reply_time = time.strftime('%Y-%m-%d %H:%M:%S')
        with transaction.atomic():
            FirstLevelReply.objects.filter(id=first_level_reply_id).update(replyCount=F('replyCount')+1)  # 总回复数+1
            second_level_reply = SecondLevelReply.objects.create(
                firstLevelReplyId=first_level_reply_id,
                postId=postid, userId=userid,
                content=content, replyTime=reply_time,
                editStatus=0)
            if utils.get(ReplyReply, firstLevelReplyId=first_level_reply_id) is None:  # 未回复过
                ReplyReply.objects.create(postId=postid, firstLevelReplyId=first_level_reply_id, userId=userid)
                FirstLevelReply.objects.filter(id=first_level_reply_id)\
                    .update(replyUserCount=F('replyUserCount')+1)  # 独立回复数+1
                _update_reply_score(first_level_reply_id)
            ret = utils.wrap_message(data={"secondLevelReplyId": second_level_reply.id},
                                     code=0, msg="发表二级回复成功")
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
def first_level_reply_list(request):
    postid = request.GET.get("postId")
    page = request.GET.get("page")
    if postid is None or page is None:
        ret = utils.wrap_message(code=1)
    else:
        page = int(page)
        start = (page - 1) * consts.FIRST_LEVEL_REPLY_LOAD_SIZE
        end = start + consts.FIRST_LEVEL_REPLY_LOAD_SIZE
        if request.GET.get("hot") == "True":  # 按热度排序
            first_level_replies = FirstLevelReply.objects.filter(postId=postid).order_by("-score")[start:end]
            logger.info("hottest first_level_replies %d:[%d, %d]", len(first_level_replies), start, end)
        else:  # 按时间排序
            first_level_replies = FirstLevelReply.objects.filter(postId=postid).order_by("-replyTime")[start:end]
            logger.info("first_level_replies %d:[%d, %d]", len(first_level_replies), start, end)
        ret = utils.wrap_message({'size': len(first_level_replies)})
        ret['list'] = [e.to_json(_fill_user_info(e.userId)) for e in first_level_replies]
    return HttpResponse(json.dumps(ret, default=utils.datetimeHandler), mimetype='application/json')


@login_required
def second_level_reply_list(request):
    first_level_reply_id = request.GET.get("firstLevelReplyId")
    page = request.GET.get("page")
    if first_level_reply_id is None or page is None:
        ret = utils.wrap_message(code=1)
    else:
        page = int(page)
        start = (page - 1) * consts.SECOND_LEVEL_REPLY_LOAD_SIZE
        end = start + consts.SECOND_LEVEL_REPLY_LOAD_SIZE
        second_level_replies = SecondLevelReply.objects.filter(
            firstLevelReplyId=first_level_reply_id).order_by("replyTime")[start:end]
        logger.info("second_level_replies %d:[%d, %d]", len(second_level_replies), start, end)
        ret = utils.wrap_message({'size': len(second_level_replies)})
        ret['list'] = [e.to_json(_fill_user_info(e.userId)) for e in second_level_replies]
    return HttpResponse(json.dumps(ret, default=utils.datetimeHandler), mimetype='application/json')


def _push_message_to_app(post):
    logger.info("pushMessageToApp")
    post_push.pushMessageToApp(post)


def _fill_user_info(userid):
    nickname = None
    avatar = None
    try:
        user_info = UserInfo.objects.get(userId=userid)
        nickname = user_info.nickname
        avatar = user_info.avatar
    except UserInfo.DoesNotExist:
        logger.warn("User or Userinfo not found")
    jsond = {"id": userid,
             "avatar": avatar,
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


# TODO: 需要原子操作
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


def _update_reply_score(_id):
    FirstLevelReply.objects.filter(id=_id).update(score=F('upCount')+F('replyUserCount'))


def redis(request):
    cache.set('foo', 'value', timeout=25)
    logger.info("redis: " + cache.get('foo') + ", " + str(cache.ttl('foo')))
    ret = utils.wrap_message(code=0)
    return HttpResponse(json.dumps(ret), mimetype='application/json')
