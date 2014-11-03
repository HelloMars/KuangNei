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
from django.contrib.auth import authenticate

from models import UserInfo
from kuangnei import consts
from main import views


TEST_USER0 = '15658076066'
TEST_USER1 = '18910690027'
TEST_USER2 = '15877444771'
TEST_PASSWORD = '~!@#`123qwer'
TEST_TOKEN0 = 'd8ee807a6da4c9a3019f3f4ce168376f'
TEST_TOKEN1 = 'af6ce77d4b57c2debef360c1bcf35190'
TEST_AVATAR = 'http://kuangnei.qiniudn.com/xxx'
TEST_DEVICEID = 'A100003B7D1E8E5'
TEST_BIRTHDAY = 123456789
TEST_NICKNAME = 'ndsun'
TEST_SEX = 1
TEST_AVATAR = 'www.kuangnei.me.com'
TEST_IMG_URL = 'www.baidu.com@www.163.com@www.sohu.com'
TEST_SIGN = '我可没时间陪你玩游戏'
TEST_SHCOOLID = 1
TEST_CHINNALID = 1


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
        # register test user 2
        self.client.post('/kuangnei/api/register/',
                         {'username': TEST_USER1,
                         'password': TEST_PASSWORD})
        # register test user 2
        self.client.post('/kuangnei/api/register/',
                         {'username': TEST_USER2,
                         'password': TEST_PASSWORD})

        # signin test user 0
        self.client.post('/kuangnei/api/signin/',
                         {'username': TEST_USER0,
                         'password': TEST_PASSWORD})
        #addUesrInfo
        self.client.post('/kuangnei/api/addUserInfo/',
                         {'avatar': TEST_AVATAR,
                         'nickname': TEST_NICKNAME,
                         'birthday': TEST_BIRTHDAY,
                         'sex': TEST_SEX,
                         'sign': TEST_SIGN,
                         'schoolId': TEST_SHCOOLID})
        #post
        self.client.post('/kuangnei/api/post/',
                         {'channelid': TEST_CHINNALID,
                          'content': '这是第一条帖子',
                          'imageurl': TEST_IMG_URL})

        self.client.post('/kuangnei/api/post/',
                         {'channelid': TEST_CHINNALID,
                          'content': u'这是第二条帖子',
                          'imageurl': TEST_IMG_URL})

        # signin user2
        self.client.post('/kuangnei/api/signin/',
                         {'username': TEST_USER2,
                         'password': TEST_PASSWORD})
         #addUesrInfo
        self.client.post('/kuangnei/api/addUserInfo/',
                         {'avatar': TEST_AVATAR,
                         'nickname': TEST_NICKNAME,
                         'birthday': TEST_BIRTHDAY,
                         'sex': TEST_SEX,
                         'sign': TEST_SIGN,
                         'schoolId': TEST_SHCOOLID})

        #first_level_reply
        self.client.post('/kuangnei/api/replyFirstLevel/',
                         {'postId': 1,
                         'content': '回复第一条帖子，这是个一级回复'})
        self.client.post('/kuangnei/api/replyFirstLevel/',
                         {'postId': 2,
                         'content': '回复第二条帖子，这是个一级回复'})
        # signin user1
        self.client.post('/kuangnei/api/signin/',
                         {'username': TEST_USER1,
                         'password': TEST_PASSWORD})

        self.client.post('/kuangnei/api/replySecondLevel/',
                         {'postId': 1,
                         'firstLevelReplyId': 1,
                         'content': '回复第一条帖子的第一个一级回复，这是个二级回复'})
        # signin user2
        self.client.post('/kuangnei/api/signin/',
                         {'username': TEST_USER2,
                         'password': TEST_PASSWORD})

        self.client.post('/kuangnei/api/replySecondLevel/',
                         {'postId': 1,
                         'firstLevelReplyId': 1,
                         'secondLevelReplyId': 2,
                         'content': '回复第一条帖子的第一个，这是个二级回复'})


    def _get_user(self, username, password):
        return authenticate(username=username, password=password)

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

    def test_post_list(self):
        response = self.client.get('/kuangnei/api/postlist/?channelid=1&page=1')
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        try:
            post = jsond['list'][1]
            self.assertEqual(post['postId'], 1)
            self.assertEqual(post['channelId'], 1)
            self.assertEqual(post['schoolId'], 1)

            self.assertIsNotNone(post['postTime'])
            self.assertIsNotNone(post['pictures'])
            self.assertEqual(post['content'], u'这是第一条帖子')

            self.assertEqual(post['replyCount'], 1)
            self.assertEqual(post['replyUserCount'], 1)
            self.assertEqual(post['upCount'], 0)
            self.assertEqual(post['opposedCount'], 0)

            user = post['user']
            self.assertEqual(1, user['id'])
            self.assertEqual(user['avatar'], TEST_AVATAR)
            self.assertEqual(user['name'], TEST_NICKNAME)
        except KeyError as e:
            self.assertIsNone(e)

    def reply_list(self):
        response = self.client.get('/kuangnei/api/firstLevelReplyList/?postId=1&page=1')
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        try:
            self.assertEqual(jsond['size'], 1)
            self.assertEqual(jsond['content'], u'回复第一条帖子，这是个一级回复')
            self.assertEqual(jsond['replyCount'], 2)

            first_level_reply = jsond['list'][0]
            self.assertEqual(first_level_reply['firstLevelReplyId'], 1)
            self.assertEqual(first_level_reply['postId'], 1)
            self.assertEqual(first_level_reply['postId'], 1)
            user = first_level_reply['user']

            self.assertIsNotNone(post['postTime'])
            self.assertIsNotNone(post['pictures'])
            self.assertEqual(post['content'], u'这是第一条帖子')

            self.assertEqual(post['replyCount'], 1)
            self.assertEqual(post['replyUserCount'], 1)
            self.assertEqual(post['upCount'], 0)
            self.assertEqual(post['opposedCount'], 0)

            user = post['user']
            self.assertEqual(1, user['id'])
            self.assertEqual(user['avatar'], TEST_AVATAR)
            self.assertEqual(user['name'], TEST_NICKNAME)
        except KeyError as e:
            self.assertIsNone(e)

    # need login
    def test_post_and_reply(self):
        # test post
        response = self.client.get('/kuangnei/api/post/')
        self._test_failed_message(response)
        response = self.client.post('/kuangnei/api/post/',
                                    {'channelid': 1,
                                     'content': 'unit test, 单元测试'})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(1, jsond['postId'])
        # forbid user
        views.forbid_user(self._get_user(TEST_USER0, TEST_PASSWORD))
        response = self.client.post('/kuangnei/api/post/',
                                    {'channelid': 1,
                                     'content': '禁言测试'})
        self.assertEqual(response.status_code, 403)
        # unforbid user
        views.unforbid_user(self._get_user(TEST_USER0, TEST_PASSWORD))
        response = self.client.post('/kuangnei/api/post/',
                                    {'channelid': 1,
                                     'content': '排序测试'})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(2, jsond['postId'])

        # test up_post and oppose_post
        # TODO: concurrent up
        # self up/oppose failed
        response = self.client.post('/kuangnei/api/uppost/',
                                    {'postId': 1})
        self._test_failed_message(response)

        response = self.client.post('/kuangnei/api/opposepost/',
                                    {'postId': 1})
        self._test_failed_message(response)

        # signin user 2
        self.client.post('/kuangnei/api/signin/',
                         {'username': TEST_USER2,
                         'password': TEST_PASSWORD})

        response = self.client.post('/kuangnei/api/uppost/',
                                    {'postId': 1})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(1, jsond['upCount'])
        # test cancel up
        response = self.client.post('/kuangnei/api/uppost/',
                                    {'postId': 1})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(0, jsond['upCount'])
        self.client.post('/kuangnei/api/uppost/', {'postId': 1})

        response = self.client.post('/kuangnei/api/opposepost/',
                                    {'postId': 1})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(1, jsond['opposedCount'])
        # test cancel oppose
        response = self.client.post('/kuangnei/api/opposepost/',
                                    {'postId': 1})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(0, jsond['opposedCount'])
        self.client.post('/kuangnei/api/opposepost/', {'postId': 1})

        # reply post and up_reply
        response = self.client.post('/kuangnei/api/replyFirstLevel/',
                                    {'postId': 1,
                                     'content': '一级回复0'})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(1, jsond['firstLevelReplyId'])
        self.client.post('/kuangnei/api/replyFirstLevel/', {'postId': 1, 'content': '一级回复1'})

        response = self.client.post('/kuangnei/api/upreply/',
                                    {'firstLevelReplyId': 1})
        self._test_failed_message(response)

        # signin user 0
        self.client.post('/kuangnei/api/signin/',
                         {'username': TEST_USER0,
                         'password': TEST_PASSWORD})

        response = self.client.post('/kuangnei/api/upreply/',
                                    {'firstLevelReplyId': 1})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(1, jsond['upCount'])
        # test cancel upreply
        response = self.client.post('/kuangnei/api/upreply/',
                                    {'firstLevelReplyId': 1})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(0, jsond['upCount'])
        self.client.post('/kuangnei/api/upreply/', {'firstLevelReplyId': 1})

        # reply comments
        response = self.client.post('/kuangnei/api/replySecondLevel/',
                                    {'postId': 1,
                                     'firstLevelReplyId': 1,
                                     'content': '二级回复0'})
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(1, jsond['secondLevelReplyId'])
        self.client.post('/kuangnei/api/replySecondLevel/',
                         {'postId': 1,
                          'firstLevelReplyId': 1,
                          'content': '二级回复1'})

        # test postlist
        response = self.client.get('/kuangnei/api/postlist/')
        self._test_failed_message(response)
        # test newest post
        response = self.client.get('/kuangnei/api/postlist/?channelid=' +
                                   str(consts.NEWEST_CHANNEL_ID) + '&page=1')
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(2, jsond['size'])  # use test database
        try:
            post = jsond['list'][0]
            self.assertEqual(post['postId'], 2)
            self.assertEqual(post['channelId'], 1)
            self.assertEqual(post['schoolId'], 1)

            self.assertIsNotNone(post['postTime'])
            self.assertIsNotNone(post['pictures'])
            self.assertEqual(post['content'], u'排序测试')

            self.assertEqual(post['replyCount'], 0)
            self.assertEqual(post['replyUserCount'], 0)
            self.assertEqual(post['upCount'], 0)
            self.assertEqual(post['opposedCount'], 0)
            self.assertEqual(post['score'], 0)

            user = post['user']
            self.assertLess(0, user['id'])
            self.assertEqual(user['avatar'], TEST_AVATAR)
            self.assertEqual(user['name'], TEST_NICKNAME)
        except KeyError as e:
            self.assertIsNone(e)
        # test hottest post
        response = self.client.get('/kuangnei/api/postlist/?channelid=' +
                                   str(consts.HOTTEST_CHANNEL_ID) + '&page=1')
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(2, jsond['size'])  # use test database
        try:
            post = jsond['list'][0]
            self.assertEqual(post['postId'], 1)
            self.assertEqual(post['channelId'], 1)
            self.assertEqual(post['schoolId'], 1)

            self.assertIsNotNone(post['postTime'])
            self.assertIsNotNone(post['pictures'])
            self.assertEqual(post['content'], u'unit test, 单元测试')

            self.assertEqual(post['replyCount'], 2)
            self.assertEqual(post['replyUserCount'], 1)
            self.assertEqual(post['upCount'], 1)
            self.assertEqual(post['opposedCount'], 1)
            self.assertLess(0, post['score'])

            user = post['user']
            self.assertLess(0, user['id'])
            self.assertEqual(user['avatar'], TEST_AVATAR)
            self.assertEqual(user['name'], TEST_NICKNAME)
        except KeyError as e:
            self.assertIsNone(e)

        # first level reply list
        response = self.client.get('/kuangnei/api/firstLevelReplyList/?postId=1&page=1')
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(2, jsond['size'])
        try:
            post = jsond['list'][0]
            self.assertEqual(post['postId'], 1)
            self.assertEqual(post['firstLevelReplyId'], 1)
            self.assertEqual(post['floor'], 1)

            self.assertIsNotNone(post['replyTime'])
            self.assertEqual(post['content'], u'一级回复0')

            self.assertEqual(post['replyCount'], 2)
            self.assertEqual(post['replyUserCount'], 1)
            self.assertEqual(post['upCount'], 1)
            self.assertEqual(post['score'], 2)

            user = post['user']
            self.assertLess(0, user['id'])
            self.assertIsNone(user['avatar'])  # user 2
            self.assertIsNotNone(user['name'])  # user 2
        except KeyError as e:
            self.assertIsNone(e)

        # second level reply list
        response = self.client.get('/kuangnei/api/secondLevelReplyList/?firstLevelReplyId=1&page=1')
        self._test_suc_message(response)
        jsond = json.loads(response.content)
        self.assertEqual(2, jsond['size'])
        try:
            post = jsond['list'][0]
            self.assertEqual(post['postId'], 1)
            self.assertEqual(post['firstLevelReplyId'], 1)
            self.assertEqual(post['secondLevelReplyId'], 1)

            self.assertIsNotNone(post['replyTime'])
            self.assertEqual(post['content'], u'二级回复0')

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
                                     'password': 'wrongPassword'})
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

        #test myPost
        response = self.client.get('/kuangnei/api/myPost/')
        self.assertEqual(response.status_code, 200)

         #test myReply
        response = self.client.get('/kuangnei/api/myReply/')
        self.assertEqual(response.status_code, 200)

         #test replyToMine
        response = self.client.get('/kuangnei/api/replyToMine/')
        self.assertEqual(response.status_code, 200)

