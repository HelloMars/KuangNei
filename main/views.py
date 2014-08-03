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

def category(request):
    foos = {
        'size': 2,
        'list': [
            {'title': '兴趣','subtitle': '不有趣可能会被踢得很惨哦'},
            {'title': '缘分','subtitle': '约会、表白、同性异性不限'}
        ]
    }
    data = simplejson.dumps(foos)
    return HttpResponse(data, mimetype='application/json')

def postlist(request):
    foos = {
        'size': 2,
        'list': [
            {
                'state': 0,
                'postId': 1234,
                'title': '',
                'shortContent': '紫金港擒鬼记',
                'postTime': time.strftime('%Y-%m-%d, %H:%M:%S',time.localtime(time.time())),
                'replyCount': 12,
                'opposedCount': 2,
                'smallPictures': [
                    'http://182.92.100.49/media/kuangnei.jpg',
                    'http://182.92.100.49/media/python.jpg',
                ],
                'bigPictures': [
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
                'state': 0,
                'postId': 1234,
                'title': '',
                'shortContent': '大姨妈侧漏了。。。',
                'postTime': time.strftime('%Y-%m-%d, %H:%M:%S',time.localtime(time.time())),
                'replyCount': 1000,
                'opposedCount': 1,
                'smallPictures': [
                    'http://182.92.100.49/media/kuangnei.jpg',
                    'http://182.92.100.49/media/python.jpg',
                ],
                'bigPictures': [
                    'http://182.92.100.49/media/kuangnei.jpg',
                    'http://182.92.100.49/media/python.jpg',
                ],
                'user': {
                    'id': 1111,
                    'name': 'lucy',
                    'avatar': 'http://182.92.100.49/media/kuangnei.jpg',
                }
            },
            {
                    'state': 1,
            }
        ]
    }
    data = simplejson.dumps(foos)
    return HttpResponse(data, mimetype='application/json')

def pushMessageToApp(request):
    demo.pushMessageToApp()
    return HttpResponse({}, mimetype='application/json')

if __name__ == '__main__':
    print "你好"
