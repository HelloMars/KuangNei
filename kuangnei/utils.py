#!/usr/bin/python
# -*- coding: UTF-8 -*-

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger("kuangnei")

import re
from qiniu import conf
from qiniu import rs

import consts

conf.ACCESS_KEY = consts.QINIU_ACCESS_KEY
conf.SECRET_KEY = consts.QINIU_SECRET_KEY

import time
import math
import json
from datetime import datetime
from datetime import date

datetimeHandler = lambda obj: obj.strftime('%Y-%m-%d %H:%M:%S')\
    if isinstance(obj, datetime) else json.JSONEncoder().default(obj)

dateHandler = lambda obj: obj.strftime('%Y-%m-%d')\
    if isinstance(obj, date) else json.JSONEncoder().default(obj)


def wrap_message(data=None, code=0, msg=''):
    ret = {'returnCode': code}
    if code == 0 and data is not None:
        ret.update(data)
    # 约定的 returnCode 与 returnMessage 映射表
    ret['returnMessage'] = {
        1: 'incorrect parameters. ',
        2: 'incorrect request method [GET, POST]. ',
        10: 'user system error. ',
        11: 'incorrect format of parameters. ',
        20: 'illegal operation. ',
    }.get(code, '') + msg
    logger.info("Return Message: " + str(ret))
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


def get(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


def cal_post_score(r, z, c):
    x = r + z - c
    if x == 0:
        m = 1
        y = 0
    else:
        m = abs(x)
        if x > 0:
            y = 1
        else:
            y = -1
    dt = time.time() - consts.BASE_TIME
    score = (dt * y) / consts.SIX_HOUR_SECONDS + math.log(m, 2)
    logger.info("Post Score: " + str(score))
    return score
