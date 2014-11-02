# -*- coding: utf-8 -*-
import calendar
from datetime import datetime
from django.contrib.auth.models import User
from django.db import models
from django.forms import model_to_dict

from kuangnei import utils

# Create your models here.


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')


class Choice(models.Model):
    question = models.ForeignKey(Question)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)


class SchoolInfo(models.Model):
    name = models.CharField(max_length=200)
    area = models.CharField(max_length=200)
    position = models.CharField(max_length=5000)

    class Meta:
        db_table = "school_info"

    def to_json(self):
        ret = {}
        for field in self._meta.fields:
            attr = field.name
            if attr != 'position':
                ret[attr] = getattr(self, attr)
        return ret

    def to_json2(self):
        ret = {}
        for field in self._meta.fields:
            attr = field.name
            ret[attr] = getattr(self, attr)
        return ret


class UserId(models.Model):
    currentId = models.IntegerField(default=0)

    class Meta:
        db_table = "user_id"


class Post(models.Model):
    user = models.ForeignKey(User, db_constraint=False)
    schoolId = models.IntegerField(db_column="school_id")
    content = models.CharField(max_length=800)
    channelId = models.IntegerField(db_column="channel_id")
    opposedCount = models.IntegerField(db_column="opposed_count")
    upCount = models.IntegerField(db_column="up_count")
    postTime = models.DateTimeField('date published', db_column="create_time")
    replyCount = models.IntegerField(db_column="reply_count")
    replyUserCount = models.IntegerField(db_column="reply_user_count")
    score = models.FloatField(db_column="score")
    imageUrls = models.CharField(db_column="image_urls", max_length=1000, null=True)
    editStatus = models.IntegerField(db_column="edit_status")

    class Meta:
        db_table = "post"

    def tojson(self, user):
        ret = {}
        for field in self._meta.fields:
            attr = field.name
            if attr == 'id':
                ret['postId'] = getattr(self, attr)
            elif attr == "user":
                ret['user'] = user
            elif attr == "imageUrls":
                image_url = getattr(self, attr)
                if image_url is not None:
                    ret['pictures'] = image_url.split("@")
                else:
                    ret['pictures'] = []
            else:
                ret[attr] = getattr(self, attr)
        return ret


# class PostPicture(models.Model):
#     #postId = models.BigIntegerField(db_column="post_id")
#     post = models.ForeignKey(Post)
#     pictureUrl = models.URLField(db_column="picture_url")
#
#     class Meta:
#         db_table = "post_picture"


class UserInfo(models.Model):
    FEMALE = 0
    MALE = 1
    NEUTRAL = 2
    DEFAULT = 3
    SEX_CHOICES = (
        (FEMALE, 'Female'),
        (MALE, 'Male'),
        (NEUTRAL, 'Neutral'),
        (DEFAULT, 'Null')
    )
    user = models.ForeignKey(User, db_constraint=False)
    schoolId = models.ForeignKey(SchoolInfo, db_column="school_id", db_constraint=False)
    deviceId = models.CharField(max_length=255, db_column="device_id", null=True)
    token = models.CharField(max_length=255, db_column="user_token", null=True)
    nickname = models.CharField(max_length=255, db_column='nickname')
    telephone = models.CharField(max_length=50, db_column="telephone")
    avatar = models.CharField(max_length=255, db_column="avatar", null=True)
    sex = models.IntegerField(db_column="sex", choices=SEX_CHOICES, default=DEFAULT)
    birthday = models.BigIntegerField(db_column="birthday", null=True)
    sign = models.CharField(max_length=255, db_column="sign", null=True)

    class Meta:
        db_table = "user_info"

    def setattrs(self, data):
        modify = False
        for field in self._meta.fields:
            attr = field.name
            value = data.get(attr.lower())
            # #生日由long转化为时间类型
            # if attr == "birthday" and value is not None:
            #     print value
            #     value = datetime.fromtimestamp((long(value))/1e3)
            # 非空并不等才更新
            if value is not None and value != getattr(self, attr):
                if attr == 'telephone' and not utils.is_avaliable_phone(value):
                    continue
                setattr(self, attr, value)
                modify = True
        return modify

    @property
    def tojson(self):
        ret = {}
        for field in self._meta.fields:
            attr = field.name
            if attr == "user":
                user = getattr(self, "user")
                ret["userId"] = user.id
            elif attr == "schoolId":
                pass
            else:
                ret[attr] = getattr(self, attr)
        return ret


class Reply(models.Model):
    post = models.ForeignKey(Post, db_constraint=False)
    fromUser = models.ForeignKey(User, related_name='fromUser', db_constraint=False)
    toUser = models.ForeignKey(User, related_name='toUser', db_constraint=False)
    content = models.CharField(db_column="content", max_length=800)
    upCount = models.IntegerField(db_column="up_count")
    replyTime = models.DateTimeField(db_column="create_time")
    hasRead = models.IntegerField(db_column='has_read')
    editStatus = models.IntegerField(db_column="edit_status")

    class Meta:
        db_table = "reply"

    def to_json(self, from_user, to_user):
        ret = {}
        for field in self._meta.fields:
            attr = field.name
            if attr == 'id':
                ret['ReplyId'] = getattr(self, attr)
            if attr == 'post':
                ret['postId'] = self.post.id
            elif attr == "fromUser":
                ret['fromUser'] = from_user
            elif attr == "toUser":
                ret['toUser'] = to_user
            else:
                ret[attr] = getattr(self, attr)
        return ret

    def to_reply_json(self, from_user, to_user, post):
        ret = {}
        for field in self._meta.fields:
            attr = field.name
            if attr == 'id':
                ret['ReplyId'] = getattr(self, attr)
            if attr == 'post':
                ret['post'] = post
            elif attr == "fromUser":
                ret['fromUser'] = from_user
            elif attr == "toUser":
                ret['toUser'] = to_user
            else:
                ret[attr] = getattr(self, attr)
        return ret


class UpPost(models.Model):
    postId = models.IntegerField(db_column="post_id")
    userId = models.IntegerField(db_column="user_id")

    class Meta:
        db_table = "up_post"
        unique_together = ("postId", "userId")


class OpposePost(models.Model):
    postId = models.IntegerField(db_column="post_id")
    userId = models.IntegerField(db_column="user_id")

    class Meta:
        db_table = "oppose_post"
        unique_together = ("postId", "userId")


class UpReply(models.Model):
    postId = models.IntegerField(db_column="post_id")
    ReplyId = models.IntegerField(db_column="reply_id", db_index=True)
    userId = models.IntegerField(db_column="user_id")

    class Meta:
        db_table = "up_reply"
        unique_together = ("ReplyId", "userId")


class Version(models.Model):
    versionNumber = models.IntegerField(db_column="version_number", primary_key=True)
    url = models.CharField(max_length=1000)
    description = models.CharField(max_length=200)

    class Meta:
        db_table = "version"

    def to_json(self):
        ret = {}
        for field in self._meta.fields:
            attr = field.name
            ret[attr] = getattr(self, attr)
        return ret


class FeedBack(models.Model):
    user = models.ForeignKey(User, db_constraint=False)
    content = models.CharField(max_length=800)

    class Meta:
        db_table = "feed_back"
