#!/usr/bin/python
# -*- coding: UTF-8 -*-

from django.core import serializers
from django.http import HttpResponse
from main.models import Post, Post_picture
import post_push
import time
import json

# Create your views here.

# test qiniu
from qiniu import conf
from qiniu import rs

conf.ACCESS_KEY = "qZUvN3pdML7x0pa4LPoP2iLI5iif0DP1l5JLx1Ax"
conf.SECRET_KEY = "oPFZOqG6dV2cuX1krZsLT1vkDBVeEzaUKYZYuQsc"
DN_DOMAIN = "kuangnei.qiniudn.com"

def getUpToken(request):
    policy = rs.PutPolicy("kuangnei")
    uptoken = policy.token()
    print uptoken
    if uptoken is None:
        backmessage = {
                       "returnCode": 1,
                       'returnMessage': '上传图片失败',
                       'uptoken': '',
                       }
    else:
        backmessage = {
                       "returnCode": 0,
                       'returnMessage': '',
                       'uptoken': uptoken,
                       }
    return HttpResponse(json.dumps(backmessage), mimetype='application/json')

def getDnToken(request):
    key = request.GET.get("key", 0)
    print key
    if key != 0:
        base_url = rs.make_base_url(DN_DOMAIN, key)
        policy = rs.GetPolicy()
        private_url = policy.make_request(base_url)
        if private_url is not None:
            backmessage = {
                           "returnCode": 0,
                           'returnMessage': '',
                           'private_url': private_url,
                           }
            return HttpResponse(json.dumps(backmessage), mimetype='application/json')
    backmessage = {
                   "returnCode": 1,
                   'returnMessage': '下载授权失败',
                   'private_url': '',
                   }
    return HttpResponse(json.dumps(backmessage), mimetype='application/json')     
    

#===============================================================================
# def post(request):
#     foos = {
#         'returnCode': 0,
#         'returnMessage': '',
#         'postId': 2,
#     }
#     data = json.dumps(foos)
#     return HttpResponse(data, mimetype='application/json')
#===============================================================================

def post(request):
    userId = request.POST.get("userid",0)
    channelId = request.POST.get("channelid",0)
    print userId
    print channelId
    if (userId != 0 and channelId != 0):
        con = request.POST.get("content","")
        post= Post(user_id = userId,school_id = 1,content = con,channel = channelId,         #插入post表
                   unlike_count = 0,create_time = time.strftime('%Y-%m-%d %H:%M:%S'),
                   back_count = 0,current_floor = 1,rank = 1,edit_status = 0)
        post.save()
        print post.id
        imageurl = request.POST.get("imageurl","")
        if imageurl != "":
            imageurlList = imageurl.split("@")
            for each in imageurlList:
                post_picture = Post_picture(picture_url = each,create_time = time.strftime('%Y-%m-%d %H:%M:%S'),
                                        post_id = post.id)
                post_picture.save()
        pushMessageToApp(post)
        backmessage = {
                       "returnCode":0,
                       'returnMessage': '',
                       'postId': post.id,
                       }
    else:
        backmessage = {
                       "returnCode":1,
                       'returnMessage': '发帖失败',
                       'postId': 0,
                       }
     
    return HttpResponse(json.dumps(backmessage))

def postlisttest(request):
    size = 5
    userId = request.GET.get("userid",0)
    channelId = request.GET.get("channelid",0)
    page = request.GET.get("page",0)
    if (userId != 0 and channelId != 0):
        postlist = Post.objects.filter(channel = channelId).order_by("-create_time")[page:size]
        postJsonList = []
        for eachpost in postlist:
            postJsonList.append(eachpost)
        foos = serializers.serialize('json',postlist)
        print foos
        backmessage = {'returnCode': 0,
                  'returnMessage': '',
                  'size': size,
                 }
    else:
        backmessage = {'returnCode': 1,
                  'returnMessage': '数据有误',
                 }
    data = json.dumps(backmessage)
    return HttpResponse(data,foos, mimetype='application/json')
       
        
    
def channellist(request):
    foos = {
        'returnCode': 0,
        'returnMessage': '',
        'size': 2,
        'list': [
            {'id': 0, 'title': '兴趣','subtitle': '不有趣可能会被踢得很惨哦'},
            {'id': 1, 'title': '缘分','subtitle': '约会、表白、同性异性不限'}
        ]
    }
    data = json.dumps(foos)
    return HttpResponse(data, mimetype='application/json')

def postlist(request):
    foos = {
        'returnCode': 0,
        'returnMessage': '',
        'size': 2,
        'list': [
            {
                'postId': 1234,
                'title': '',
                'content': '紫金港擒鬼记',
                'postTime': time.strftime('%Y-%m-%d, %H:%M:%S',time.localtime(time.time())),
                'replyCount': 12,
                'opposedCount': 2,
                'upCount': 5,
                'pictures': [
                    'http://182.92.100.49/media/kuangnei.jpg',
                    'http://182.92.100.49/media/python.jpg',
                ],
                'user': {
                    'id': 4321,
                    'name': 'van',
                    'avatar': 'http://182.92.100.49/media/kuangnei.jpg',
                }
            },
            {
                'postId': 1234,
                'title': '',
                'content': '大姨妈侧漏了。。。',
                'postTime': time.strftime('%Y-%m-%d, %H:%M:%S',time.localtime(time.time())),
                'replyCount': 1000,
                'opposedCount': 1,
                'upCount': 333,
                'pictures': [
                    'http://182.92.100.49/media/kuangnei.jpg',
                    'http://182.92.100.49/media/python.jpg',
                ],
                'user': {
                    'id': 1111,
                    'name': 'lucy',
                    'avatar': 'http://182.92.100.49/media/kuangnei.jpg',
                }
            },
        ]
    }
    data = json.dumps(foos)
    return HttpResponse(data, mimetype='application/json')

def pushMessageToApp(post):
    post_push.pushMessageToApp(post)
    
if __name__ == '__main__':
    print "你好"
