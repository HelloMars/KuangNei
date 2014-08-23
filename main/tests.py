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


class ApiTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

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

    def test_post_and_postlist(self):
        # test post
        response = self.client.get('/kuangnei/api/post/')
        self._test_failed_message(response)
        response = self.client.post('/kuangnei/api/post/',
                                    {'userid': 1,
                                     'channelid': 1,
                                     'content': 'unit test, 单元测试'})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertLess(0, jsond['postId'])

        # test postlist
        response = self.client.get('/kuangnei/api/postlist/')
        self._test_failed_message(response)
        response = self.client.get('/kuangnei/api/postlist/?userid=1&channelid=1&page=1')
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
            self.assertEqual(user['id'], u'1')
            self.assertIsNotNone(user['avatar'])
            self.assertIsNotNone(user['name'])
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
                                    {'username': '18910690027',
                                     'password': '~!@#`123qwer',
                                     'token': ''})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(jsond['user'], '18910690027')

        # test exist
        response = self.client.post('/kuangnei/api/checkIfUserExist/',
                                    {'username': '18910690027'})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertTrue(jsond['exist'])
        response = self.client.post('/kuangnei/api/checkIfUserExist/',
                                    {'username': 'kuang'})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertFalse(jsond['exist'])

        # test login_in
        response = self.client.get('/kuangnei/api/signin/')
        self._test_failed_message(response)
        # password error
        response = self.client.post('/kuangnei/api/signin/',
                                    {'username': '18910690027',
                                     'password': ''})
        self._test_failed_message(response)
        # successful
        response = self.client.post('/kuangnei/api/signin/',
                                    {'username': '18910690027',
                                     'password': '~!@#`123qwer'})
        self._test_suc_message(response)

        # test add user info
        response = self.client.post('/kuangnei/api/addUserInfo/',
                                    {'avatar': 'http://kuangnei.qiniudn.com/FjMgIjdmHH9lkUm9Ra_K1VbKynxR',
                                     'sex': UserInfo.MALE,
                                     'schoolid': 1,
                                     'sign': 'A',
                                     'telephone': '18910690027'})
        self._test_suc_message(response)

        # test login_out
        response = self.client.get('/kuangnei/api/logout/')
        self._test_suc_message(response)
