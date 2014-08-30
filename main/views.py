#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
import time

from django.contrib.auth import authenticate, logout, login, SESSION_KEY
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import redirect

from kuangnei import consts, utils
from kuangnei.utils import logger
from main.models import Post, PostPicture, UserInfo, FirstLevelResponse, SecondLevelResponse
import post_push


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
def post(request):
    if request.method != 'POST':
        ret = utils.wrap_message(code=2)
    else:
        userid = request.session[SESSION_KEY]
        channelid = request.POST.get("channelid")
        content = request.POST.get("content")
        if channelid is None or content is None:
            ret = utils.wrap_message(code=1)
        else:
            post = Post(userId=userid, schoolId=1, content=content, channelId=channelid,
                        opposedCount=0, postTime=time.strftime('%Y-%m-%d %H:%M:%S'),
                        replyCount=0, currentFloor=1, rank=1, editStatus=0, upCount=0)
            post.save()
            logger.info("post " + str(post.id))
            imageurl = request.POST.get("imageurl")
            if imageurl is not None:
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
    #userid = request.session[SESSION_KEY]
    channelid = request.GET.get("channelid")
    page = request.GET.get("page")
    if channelid is None or page is None:
        ret = utils.wrap_message(code=1)
    else:
        page = int(page)
        start = (page - 1) * consts.LOAD_SIZE
        end = start + consts.LOAD_SIZE
        postlist = Post.objects.filter(channelId=channelid).order_by("-postTime")[start:end]
        logger.info("postlist [%d, %d]", start, end)
        d = {}
        for e in postlist:
            pictures = PostPicture.objects.filter(postId=e.id).values_list("pictureUrl", flat=True)
            d[e.id] = list(pictures)
        ret = utils.wrap_message({'size': len(postlist)})
        ret['list'] = [e.tojson(d[e.id], _fill_user_info(e.userId)) for e in postlist]
    return HttpResponse(json.dumps(ret, default=utils.datetimeHandler),
                        mimetype='application/json')


def register(request):
    if request.method != 'POST':
        ret = utils.wrap_message(code=2)
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        deviceid = request.POST.get('deviceid')
        if username is None or password is None or deviceid is None:
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
                    token = request.POST.get('token')  # could be None
                    UserInfo.objects.create(userId=newuser.id, deviceId=deviceid,
                                            token=token, nickname='user'+str(newuser.id),
                                            telephone=username)
                    user = authenticate(username=username, password=password)
                    login(request, user)
                    request.session.set_expiry(300)  # session失效期5分钟
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


def _login(username, password, deviceid, token, request):
    if username is None or password is None or deviceid is None:
        ret = utils.wrap_message(code=1)
    else:
        user = authenticate(username=username, password=password)
        if user is None:
            ret = utils.wrap_message(code=10, msg='用户名或密码错误')
        else:
            if user.is_active:
                login(request, user)
                user_info = UserInfo.objects.get(userId=user.id)
                user_info.deviceId = deviceid
                if token is not None:
                    user_info.token = token
                    logger.info('修改用户(%s)token成功', repr(user.id))
                user_info.save()
                request.session.set_expiry(300)
                ret = utils.wrap_message(code=0, msg='登陆成功')
            else:
                ret = utils.wrap_message(code=10, msg='用户无权限')
    return ret


# http://127.0.0.1:8000/accounts/login/?
# next=/kuangnei/api/channellist/&username=18910690027&password=~%21%40%23%60123qwer&deviceid=xxx
def rlogin_in(request):
    username = request.GET.get('username')
    password = request.GET.get('password')
    deviceid = request.GET.get('deviceid')
    token = request.GET.get('token')
    if username is None or password is None or deviceid is None:
        raise Http404
    else:
        _login(username, password, deviceid, token, request)
        return redirect(request.GET.get('next'))


def login_in(request):
    if request.method != 'POST':
        ret = utils.wrap_message(code=2)
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        deviceid = request.POST.get('deviceid')
        token = request.POST.get('token')
        ret = _login(username, password, deviceid, token, request)
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
        'size': 2,
        'list': [
            {'id': 0, 'title': '兴趣', 'subtitle': '不有趣可能会被踢得很惨哦'},
            {'id': 1, 'title': '缘分', 'subtitle': '约会、表白、同性异性不限'}
        ]
    }
    data = json.dumps(foos)
    return HttpResponse(data, mimetype='application/json')


@login_required
def up_post(request):
    user_id = request.session[SESSION_KEY]
    post_id = request.POST.get('postid')
    if post_id is None or user_id is None:
        logger.error("参数错误")
        ret = utils.wrap_message(code=1)
    else:
        try:
            Post.objects.get(id=post_id)  # 验证post_id是有效字段
            Post.objects.filter(id=post_id).update(upCount=F('upCount')+1)
            ret = utils.wrap_message(code=0, msg="赞成功")
        except Exception as e:
            logger.error(e)
            ret = utils.wrap_message(code=1)
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
def up_reply(request):
    user_id = request.session[SESSION_KEY]
    first_level_reply_id = request.POST.get('firstLevelReplyId')
    if first_level_reply_id is None or user_id is None:
        logger.error("参数错误")
        ret = utils.wrap_message(code=1)
    else:
        try:
            FirstLevelResponse.objects.get(id=first_level_reply_id)  # 验证post_id是有效字段
            FirstLevelResponse.objects.filter(id=first_level_reply_id).update(upCount=F('upCount')+1)
            ret = utils.wrap_message(code=0, msg="赞成功")
        except Exception as e:
            logger.error(e)
            ret = utils.wrap_message(code=1)
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
def oppose_post(request):
    user_id = request.session[SESSION_KEY]
    post_id = request.POST.get('postid')
    if post_id is None or user_id is None:
        logger.error("参数错误")
        ret = utils.wrap_message(code=1)
    else:
        try:
            Post.objects.get(id=post_id)  # 验证post_id是有效字段
            Post.objects.filter(id=post_id).update(opposedCount=F('opposedCount')+1)
            ret = utils.wrap_message(code=0, msg="踩成功")
        except Exception as e:
            logger.error(e)
            ret = utils.wrap_message(code=1)
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
def reply_first_level(request):
    user_id = request.session[SESSION_KEY]
    post_id = request.POST.get('postid')
    content = request.POST.get('content')
    try:
        if post_id is None or content is None or user_id is None:
            logger.error("参数错误")
            ret = utils.wrap_message(code=1)
        else:
            response_time = time.strftime('%Y-%m-%d %H:%M:%S')
            with transaction.atomic():
                Post.objects.filter(id=post_id).update(currentFloor=F('currentFloor')+1)  # post表里对应的currentFloor加1
                current_floor = Post.objects.get(id=post_id).currentFloor
                first_level_response = FirstLevelResponse.objects.create(
                    postId=post_id, userId=user_id, upCount=0,
                    content=content, floor=current_floor,
                    replyCount=0, createTime=response_time,
                    editStatus=0)
                ret = utils.wrap_message(data={"firstLevelReplyId": first_level_response.id},
                                         code=0, msg="发表回复成功")
    except Exception as e:
        logger.error(e)
        ret = utils.wrap_message(code=1)
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
def reply_second_level(request):
    user_id = request.session[SESSION_KEY]
    post_id = request.POST.get('postid')
    first_level_res_id = request.POST.get('firstLevelResponseId')
    content = request.POST.get('content')
    try:
        if post_id is None or content is None or user_id is None or first_level_res_id is None:
            logger.error("参数错误")
            ret = utils.wrap_message(code=1)
        else:
            response_time = time.strftime('%Y-%m-%d %H:%M:%S')
            with transaction.atomic():
                Post.objects.get(id=post_id)  # 验证post_id是否是有效值
                FirstLevelResponse.objects.get(id=first_level_res_id)
                FirstLevelResponse.objects.filter(id=first_level_res_id).update(replyCount=F('replyCount')+1)
                second_level_response = SecondLevelResponse.objects.create(
                    firstLevResponseId=first_level_res_id,
                    postId=post_id, userId=user_id,
                    content=content, createTime=response_time,
                    editStatus=0)
                ret = utils.wrap_message(data={"secondLevelReplyId": second_level_response.id}, code=0, msg="发表回复成功")
    except Exception as e:
        logger.error(e)
        ret = utils.wrap_message(code=1)
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
def first_level_reply_list(request):
    post_id = request.GET.get("postid")
    page = request.GET.get("page")
    if post_id is None or page is None:
        ret = utils.wrap_message(code=1)
    else:
        page = int(page)
        start = (page - 1) * consts.FIRST_LEVEL_REPLY_LOAD_SIZE
        end = start + consts.FIRST_LEVEL_REPLY_LOAD_SIZE
        first_lev_rep_list = FirstLevelResponse.objects.filter(postId=post_id).order_by("floor")[start:end]
        logger.info("first_level_reply_list [%d, %d]", start, end)
        ret = utils.wrap_message({'size': len(first_lev_rep_list)})
        ret['list'] = [e.to_json(_fill_user_info(e.userId)) for e in first_lev_rep_list]
    return HttpResponse(json.dumps(ret, default=utils.datetimeHandler), mimetype='application/json')


@login_required
def second_level_reply_list(request):
    first_lev_rep_id = request.GET.get("firstLevelReplyId")
    page = request.GET.get("page")
    if first_lev_rep_id is None or page is None:
        ret = utils.wrap_message(code=1)
    else:
        page = int(page)
        start = (page - 1) * consts.SECOND_LEVEL_REPLY_LOAD_SIZE
        end = start + consts.SECOND_LEVEL_REPLY_LOAD_SIZE
        second_lev_rep_list = SecondLevelResponse.objects.filter(
            firstLevResponseId=first_lev_rep_id).\
            order_by("createTime")[start:end]
        logger.info("second_lev_rep_list [%d, %d]", start, end)
        ret = utils.wrap_message({'size': len(second_lev_rep_list)})
        ret['list'] = [e.to_json(_fill_user_info(e.userId)) for e in second_lev_rep_list]
    return HttpResponse(json.dumps(ret, default=utils.datetimeHandler), mimetype='application/json')


def _push_message_to_app(post):
    logger.info("pushMessageToApp")
    post_push.pushMessageToApp(post)


def _fill_user_info(userid):
    nickname = None
    avatar = None
    try:
        #user = User.objects.get(id=userid)
        user_info = UserInfo.objects.get(userId=userid)
        nickname = user_info.nickname
        avatar = user_info.avatar
    except UserInfo.DoesNotExist:
        logger.warn("User or Userinfo not found")
    jsond = {"id": userid,
             "avatar": avatar,
             "name": nickname}
    return jsond
