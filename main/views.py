#!/usr/bin/python
# -*- coding: UTF-8 -*-

from django.contrib.auth.models import User
from django.http import HttpResponse
from kuangnei import consts, utils
from kuangnei.utils import logger
from main.models import Post, Post_picture
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
    if request.method == 'POST':
        username = request.POST.get('username','')
        password = request.POST.get('password','')
        if username != "" and password != "":
            newUser = User(username=username)
            newUser.set_password(password)             #把密码加密
            newUser.save()
            backmessage = {'returnCode':0,
                           'returnMessage':'',
                           'user':newUser.username,
                           }
        else:
            backmessage = {'returnCode':1,
                            'returnMessage':'注册失败',
                            }
    else:
        backmessage = {'returnCode':1,
                        'returnMessage':'注册失败',
                           }
    return HttpResponse(json.dumps(backmessage,ensure_ascii = False))
    

def check_if_user_exist(request):
    if request.method == 'POST':
        username = request.POST.get('username','')
        user = User.objects.filter(username = username)
        if user:
            backmessage = {'returnCode':1,
                           'returnMessage':'用户已经存在',
                           }
        else:
            backmessage = {'returnCode':0,
                           'returnMessage':'',
                           }
        return HttpResponse(json.dumps(backmessage,ensure_ascii = False))
    else:
        backmessage = {'returnCode':1,
                        'returnMessage':'注册失败',
                           }
    return HttpResponse(json.dumps(backmessage,ensure_ascii = False))


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
