#!/usr/bin/python
# -*- coding: UTF-8 -*-

# import the logging library
import logging

# Get an instance of a logger
import re

logger = logging.getLogger("kuangnei")

from qiniu import conf
from qiniu import rs

import consts

conf.ACCESS_KEY = consts.QINIU_ACCESS_KEY
conf.SECRET_KEY = consts.QINIU_SECRET_KEY

from datetime import datetime
from datetime import date
import json

datetimeHandler = lambda obj: obj.strftime('%Y-%m-%d %H:%M:%S')\
    if isinstance(obj, datetime) else json.JSONEncoder().default(obj)

dateHandler = lambda obj: obj.strftime('%Y-%m-%d')\
    if isinstance(obj, date) else json.JSONEncoder().default(obj)


def wrap_message(data={}, code=0, msg=''):
    ret = {'returnCode': code, 'returnMessage': msg}
    if code == 0:
        ret.update(data)
    elif msg == '':
        ret['returnMessage'] = {
            1: 'incorrect parameters',
            2: 'incorrect request method [GET, POST]'
        }.get(code, '')
    return ret


def get_uptoken(scope):
    policy = rs.PutPolicy(scope)
    uptoken = policy.token()
    logger.info("Generate qiniu uptoken(%s) for scope(%s)", uptoken, scope)
    return uptoken


def get_dnurl(key):
    base_url = rs.make_base_url(consts.QINIU_DN_DOMAIN, key)
    policy = rs.GetPolicy()
    dnurl = policy.make_request(base_url)
    logger.info("Generate qiniu dnurl(%s) from key(%s)", dnurl, key)
    return dnurl

def is_avaliable_phone(phonenumber):
    pattern = re.compile('^1[3|5|7|8|][0-9]{9}$')
    match = pattern.match(phonenumber)
    if match:
        return True
    else:
        return False
