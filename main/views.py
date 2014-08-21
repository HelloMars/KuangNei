#!/usr/bin/python
# -*- coding: UTF-8 -*-

from django.contrib.auth import authenticate, logout, login, SESSION_KEY
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
import re
from kuangnei import consts, utils
from kuangnei.utils import logger
from main.models import Post, Post_picture, UserInfo
import json
import post_push
import time

# Create your views here.


def get_uptoken(request):
    uptoken = utils.get_uptoken(consts.QINIU_SCOP)
    ret = utils.wrap_message({'uptoken': uptoken})
    return HttpResponse(json.dumps(ret), mimetype='application/json')


def get_dnurl(request):
    key = request.GET.get("key")
    if key is None:
        ret = utils.wrap_message(code=1)
    else:
        dnurl = utils.get_dnurl(key)
        ret = utils.wrap_message({'dnurl': dnurl})
    return HttpResponse(json.dumps(ret), mimetype='application/json')


def post(request):
    if request.method != 'POST':
        ret = utils.wrap_message(code=2)
    else:
        userid = request.POST.get("userid")
        channelid = request.POST.get("channelid")
        content = request.POST.get("content")
        if userid is None or channelid is None or content is None:
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
                    post_picture = Post_picture(picture_url=url, post_id=post.id,
                                                create_time=time.strftime('%Y-%m-%d %H:%M:%S'))
                    post_picture.save()
            _push_message_to_app(post)
            ret = utils.wrap_message({'postId': post.id})
    return HttpResponse(json.dumps(ret), mimetype='application/json')


def postlist(request):
    userid = request.GET.get("userid")
    channelid = request.GET.get("channelid")
    page = request.GET.get("page")
    if userid is None or channelid is None or page is None:
        ret = utils.wrap_message(code=1)
    else:
        page = int(page)
        start = (page - 1) * consts.LOAD_SIZE
        end = start + consts.LOAD_SIZE
        postlist = Post.objects.filter(channelId=channelid).order_by("-postTime")[start:end]
        logger.info("postlist [%d, %d]", start, end)
        d = {}
        for e in postlist:
            pictures = Post_picture.objects.filter(post_id=e.id).values_list("picture_url", flat=True)
            d[e.id] = list(pictures)
        ret = utils.wrap_message({'size': len(postlist)})
        ret['list'] = [e.tojson(d[e.id], mock_user(e.userId)) for e in postlist]
    return HttpResponse(json.dumps(ret, default=utils.datetimeHandler),
                        mimetype='application/json')


def register(request):
    if request.method != 'POST':
        ret = utils.wrap_message(code=2)
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        token = request.POST.get('token')
        if username is None or password is None or token is None:
            ret = utils.wrap_message(code=1)
        else:
            olduser = User.objects.filter(username=username).first()
            if olduser is None:
                newuser = User.objects.create_user(username=username, password=password)
                if newuser is None:
                    ret = utils.wrap_message(code=10, msg='注册失败')
                    logger.warn('注册失败')
                else:
                    UserInfo.objects.create(userId=newuser.id, token=token)  #在user_info表中设置token
                    user = authenticate(username=username, password=password)
                    login(request, user)
                    request.session.set_expiry(300)     #session失效期5分钟
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


def login_in(request):
    if request.method != 'POST':
        ret = utils.wrap_message(code=2)
    else:
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username is None or password is None:
            ret = utils.wrap_message(code=1)
        else:
            user = authenticate(username=username, password=password)
            if user is None:
                ret = utils.wrap_message(code=11, msg='用户名或密码错误')
            else:
                if user.is_active:
                    login(request, user)
                    request.session.set_expiry(300)
                    ret = utils.wrap_message(code=0, msg='登陆成功')
                else:
                    ret = utils.wrap_message(code=12, msg='用户认证已过期')
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
def logout_out(request):
    logout(request)
    ret = utils.wrap_message(code=0, msg='退出成功')
    return HttpResponse(json.dumps(ret), mimetype='application/json')


@login_required
def test_view(request):
    return HttpResponse('diu')


@login_required
def add_user_info(request):
    user_id = request.session[SESSION_KEY]
    sex = request.POST.get('sex')
    schoolid = request.POST.get('schoolid')
    sign = request.POST.get('sign')
    user_info = UserInfo.objects.get(userId = user_id)
    telephone = request.POST.get('telephone')
    if telephone is not None:
        pattern = re.compile('^1[3|5|7|8|][0-9]{9}$')
        match = pattern.match(telephone)
        if match:
            user_info.telephone = telephone
        else:
            ret = utils.wrap_message(code=13, msg='电话有误')
            return HttpResponse(json.dumps(ret, ensure_ascii=False))
    if sex is not None:
        user_info.sex = sex
    if schoolid is not None:
        user_info.schoolId = schoolid
    if sign is not None:
        user_info.sign = sign
    user_info.save()
    logger.info('修改用户(%s)信息成功', repr(user_id))
    ret = utils.wrap_message(code=0,msg='修改个人信息成功')
    return HttpResponse(json.dumps(ret), mimetype='application/json')


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


def _push_message_to_app(post):
    logger.info("pushMessageToApp")
    post_push.pushMessageToApp(post)


def mock_user(userid):
    jsond = {"id": userid,
             "avatar": "http://kuangnei.qiniudn.com/FjMgIjdmHH9lkUm9Ra_K1VbKynxR",
             "name": "框内"}
    return jsond
