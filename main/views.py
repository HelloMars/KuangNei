#!/usr/bin/python
# -*- coding: UTF-8 -*-

from django.shortcuts import render

# Create your views here.

from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import HttpResponse
from django.core import serializers
from django.utils import simplejson

import time
import datetime

import demo

def post(request):
    foos = {
        'returnCode': 0,
        'returnMessage': '',
        'postId': 2,
    }
    data = simplejson.dumps(foos)
    return HttpResponse(data, mimetype='application/json')

def posttest(request):
    userId = request.META.get("userid",0)
    channelId = request.META.get("channelid",0)
    if (userId != 0 and channelId != 0):
        con = request.META.get("content",0)
        post= Post(school_id = "1",content = con,chnnal = channelId,         #插入post表
                   unlike_count = 0,create_time = time.strftime('%Y-%m-%d %H:%M:%S'),
                   back_count = 0,current_floor = 1,rank = 1)
        post.save()
        print post.id
        imageurl = request.META.get("imageurl",0)
        imageurlList = imageurl.split("@")
        for each in imageurlList:
            post_picture = Post_picture(picture_url = each,create_time = time.strftime('%Y-%m-%d %H:%M:%S'),
                                        post_id = post.id)
            post_picture.save()
        backmessage = {
                       "returncode":0,
                       'returnMessage': '',
                       'postId': post.id,
                       }
    else:
        backmessage = {
                       "returncode":1,
                       'returnMessage': '发帖失败',
                       'postId': 0,
                       }
     
    return HttpResponse(backmessage, mimetype='application/json')       
        
    
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
    data = simplejson.dumps(foos)
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
    data = simplejson.dumps(foos)
    return HttpResponse(data, mimetype='application/json')

def pushMessageToApp(request):
    demo.pushMessageToApp()
    return HttpResponse({}, mimetype='application/json')

if __name__ == '__main__':
    print "你好"
