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
    userId = request.POST.get("userid","")
    channelId = request.POST.get("channelid",0)
    print userId
    print channelId
    if (userId != "" and channelId != 0):
        con = request.POST.get("content","")
        post= Post(userId = userId,schoolId = 1,content = con,channelId = channelId,         #插入post表
                   opposedCount = 0,postTime = time.strftime('%Y-%m-%d %H:%M:%S'),
                   replyCount = 0,currentFloor = 1,rank = 1,editStatus = 0,upCount = 0)
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
     
    return HttpResponse(json.dumps(backmessage,ensure_ascii = False))

def postlist(request):
    size = 5
    userId = request.GET.get("userid",0)
    channelId = request.GET.get("channelid",0)
    page = int(request.GET.get("page",0))
    if (userId != 0 and channelId != 0):
        postlist = Post.objects.filter(channelId = channelId).order_by("-postTime")[page:page+size]
        d = {}
        for eachPost in postlist:
            pictures = Post_picture.objects.filter(post_id = eachPost.id).values_list("picture_url",flat = True)
            d[eachPost.id] = list(pictures)
            print json.dumps(list(pictures))
            print json.dumps(d)
        backmessage = {'returnCode': 0,
                       'returnMessage': '',
                       'size': size,
                       'list': [json.loads(e.toJSON(d[e.id],getUser(e.userId))) for e in postlist],
                       }
    else:
        backmessage = {'returnCode': 1,
                       'returnMessage': '数据有误',
                       }
    data = json.dumps(backmessage,ensure_ascii = False)
    return HttpResponse(data, mimetype='application/json')
       
        
    
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

# def postlist(request):
#     foos = {
#         'returnCode': 0,
#         'returnMessage': '',
#         'size': 2,
#         'list': [
#             {
#                 'postId': 1234,
#                 'title': '',
#                 'content': '紫金港擒鬼记',
#                 'postTime': time.strftime('%Y-%m-%d, %H:%M:%S',time.localtime(time.time())),
#                 'replyCount': 12,
#                 'opposedCount': 2,
#                 'upCount': 5,
#                 'pictures': [
#                     'http://182.92.100.49/media/kuangnei.jpg',
#                     'http://182.92.100.49/media/python.jpg',
#                 ],
#                 'user': {
#                     'id': 4321,
#                     'name': 'van',
#                     'avatar': 'http://182.92.100.49/media/kuangnei.jpg',
#                 }
#             },
#             {
#                 'postId': 1234,
#                 'title': '',
#                 'content': '大姨妈侧漏了。。。',
#                 'postTime': time.strftime('%Y-%m-%d, %H:%M:%S',time.localtime(time.time())),
#                 'replyCount': 1000,
#                 'opposedCount': 1,
#                 'upCount': 333,
#                 'pictures': [
#                     'http://182.92.100.49/media/kuangnei.jpg',
#                     'http://182.92.100.49/media/python.jpg',
#                 ],
#                 'user': {
#                     'id': 1111,
#                     'name': 'lucy',
#                     'avatar': 'http://182.92.100.49/media/kuangnei.jpg',
#                 }
#             },
#         ]
#     }
#     data = json.dumps(foos)
#     return HttpResponse(data, mimetype='application/json')

def pushMessageToApp(post):
    post_push.pushMessageToApp(post)

def getUser(userId):
    d = {"id":userId,
         "avatar":"http://kuangnei.qiniudn.com/FjMgIjdmHH9lkUm9Ra_K1VbKynxR",
         "name":"啊啊啊",
         }
    return d
    
    
if __name__ == '__main__':
    print "你好"
