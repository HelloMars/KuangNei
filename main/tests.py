#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import json
from django.test import TestCase
from django.test.client import Client
from django.test.client import RequestFactory

from models import UserInfo

TEST_USER0 = '15658076066'
TEST_USER1 = '18910690027'
TEST_PASSWORD = '~!@#`123qwer'
TEST_TOKEN0 = 'd8ee807a6da4c9a3019f3f4ce168376f'
TEST_TOKEN1 = 'af6ce77d4b57c2debef360c1bcf35190'
TEST_AVATAR = 'http://kuangnei.qiniudn.com/xxx'
TEST_NICKNAME = 'zavatar'
TEST_DEVICEID = 'A100003B7D1E8E5'


class ApiTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        # login test user 0
        self.client.post('/kuangnei/api/register/',
                         {'username': TEST_USER0,
                         'password': TEST_PASSWORD,
                         'deviceid': TEST_DEVICEID,
                         'token': TEST_TOKEN0})
        self.client.post('/kuangnei/api/signin/',
                         {'username': TEST_USER0,
                         'password': TEST_PASSWORD,
                         'deviceid': TEST_DEVICEID})
        self.client.post('/kuangnei/api/addUserInfo/',
                         {'avatar': TEST_AVATAR,
                         'nickname': TEST_NICKNAME})

    def _test_suc_message(self, response):
        jsond = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(jsond['returnCode'], 0)

    def _test_failed_message(self, response):
        jsond = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertLess(0, jsond['returnCode'])
        self.assertIsNotNone(jsond['returnMessage'])
        self.assertNotEqual(jsond['returnMessage'], '')

    def test_get_uptoken(self):
        response = self.client.get('/kuangnei/api/getUpToken/')
        self._test_suc_message(response)

    def test_get_dnurl(self):
        response = self.client.get('/kuangnei/api/getDnUrl/')
        self._test_failed_message(response)
        response = self.client.get('/kuangnei/api/getDnUrl/?key=image.jpg')
        self._test_suc_message(response)

    # need login
    def test_post_and_postlist(self):
        # test post
        response = self.client.get('/kuangnei/api/post/')
        self._test_failed_message(response)
        response = self.client.post('/kuangnei/api/post/',
                                    {'channelid': 1,
                                     'content': 'unit test, 单元测试'})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertLess(0, jsond['postId'])

        # test postlist
        response = self.client.get('/kuangnei/api/postlist/')
        self._test_failed_message(response)
        response = self.client.get('/kuangnei/api/postlist/?channelid=1&page=1')
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(1, jsond['size'])  # use test database
        try:
            post = jsond['list'][0]
            self.assertEqual(post['postId'], 1)
            self.assertEqual(post['channelId'], 1)
            self.assertEqual(post['schoolId'], 1)

            self.assertIsNotNone(post['postTime'])
            self.assertIsNotNone(post['pictures'])
            self.assertEqual(post['content'], u'unit test, 单元测试')

            self.assertEqual(post['replyCount'], 0)
            self.assertEqual(post['upCount'], 0)
            self.assertEqual(post['opposedCount'], 0)

            user = post['user']
            self.assertLess(0, user['id'])
            self.assertEqual(user['avatar'], TEST_AVATAR)
            self.assertEqual(user['name'], TEST_NICKNAME)
        except KeyError as e:
            self.assertIsNone(e)

    def test_channellist(self):
        response = self.client.get('/kuangnei/api/channellist/')
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertLessEqual(0, jsond['size'])
        self.assertIsNotNone(jsond['list'])

    def test_user_system(self):
        # test register
        response = self.client.get('/kuangnei/api/register/')
        self._test_failed_message(response)
        response = self.client.post('/kuangnei/api/register/',
                                    {'username': TEST_USER1,
                                     'password': TEST_PASSWORD,
                                     'deviceid': TEST_DEVICEID,
                                     'token': TEST_TOKEN0})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(jsond['user'], TEST_USER1)

        # test exist
        response = self.client.post('/kuangnei/api/checkIfUserExist/',
                                    {'username': TEST_USER1})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertTrue(jsond['exist'])
        response = self.client.post('/kuangnei/api/checkIfUserExist/',
                                    {'username': '18910690028'})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertFalse(jsond['exist'])

        # test login_in
        response = self.client.get('/kuangnei/api/signin/')
        self._test_failed_message(response)
        # password error
        response = self.client.post('/kuangnei/api/signin/',
                                    {'username': TEST_USER1,
                                     'password': 'wrongPassword',
                                     'deviceid': TEST_DEVICEID})
        self._test_failed_message(response)
        # successful
        response = self.client.post('/kuangnei/api/signin/',
                                    {'username': TEST_USER1,
                                     'password': TEST_PASSWORD,
                                     'deviceid': TEST_DEVICEID,
                                     'token': TEST_TOKEN1})
        self._test_suc_message(response)
        # get user info
        response = self.client.post('/kuangnei/api/addUserInfo/')
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        try:
            self.assertLess(0, jsond['userId'])
            self.assertEqual(jsond['token'], TEST_TOKEN1)
            self.assertIsNone(jsond['avatar'])
            self.assertEqual(jsond['nickname'], 'user'+str(jsond['userId']))
            self.assertEqual(jsond['sex'], UserInfo.DEFAULT)
            self.assertIsNone(jsond['birthday'])
            self.assertIsNone(jsond['sign'])
            self.assertIsNone(jsond['schoolId'])
            self.assertEqual(jsond['telephone'], TEST_USER1)
        except KeyError as e:
            self.assertIsNone(e)

        # test add user info
        response = self.client.post('/kuangnei/api/addUserInfo/',
                                    {'token': TEST_TOKEN0,
                                     'avatar': TEST_AVATAR,
                                     'nickname': TEST_NICKNAME,
                                     'sex': UserInfo.MALE,
                                     'birthday': '1989-01-27',
                                     'sign': 'Just do it!',
                                     'schoolid': 1,
                                     'telephone': '18910690027'})
        self._test_suc_message(response)
        # get user info
        response = self.client.post('/kuangnei/api/addUserInfo/')
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        try:
            self.assertLess(0, jsond['userId'])
            self.assertEqual(jsond['token'], TEST_TOKEN0)
            self.assertEqual(jsond['avatar'], TEST_AVATAR)
            self.assertEqual(jsond['nickname'], TEST_NICKNAME)
            self.assertEqual(jsond['sex'], UserInfo.MALE)
            self.assertEqual(jsond['birthday'], '1989-01-27')
            self.assertEqual(jsond['sign'], 'Just do it!')
            self.assertEqual(jsond['schoolId'], 1)
            self.assertEqual(jsond['telephone'], '18910690027')
        except KeyError as e:
            self.assertIsNone(e)

        # test login_out
        response = self.client.get('/kuangnei/api/logout/')
        self._test_suc_message(response)
