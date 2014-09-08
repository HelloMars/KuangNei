# -*- coding: utf-8 -*-
from django.db import models

from kuangnei import utils

# Create your models here.


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')


class Choice(models.Model):
    question = models.ForeignKey(Question)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)


class Post(models.Model):
    userId = models.IntegerField(db_column="user_id")
    schoolId = models.IntegerField(db_column="school_id")
    content = models.CharField(max_length=800)
    channelId = models.IntegerField(db_column="channel_id")
    opposedCount = models.IntegerField(db_column="opposed_count")
    upCount = models.IntegerField(db_column="up_count")
    postTime = models.DateTimeField('date published', db_column="create_time")
    replyCount = models.IntegerField(db_column="reply_count")
    replyUserCount = models.IntegerField(db_column="reply_user_count")
    score = models.FloatField(db_column="score")
    editStatus = models.IntegerField(db_column="edit_status")

    class Meta:
        db_table = "post"

    def tojson(self, image_url, user):
        ret = {}
        for field in self._meta.fields:
            attr = field.name
            if attr == 'id':
                ret['postId'] = getattr(self, attr)
            elif attr == "userId":
                ret['user'] = user
            else:
                ret[attr] = getattr(self, attr)
        ret['pictures'] = image_url
        return ret


class PostPicture(models.Model):
    postId = models.BigIntegerField(db_column="post_id")
    pictureUrl = models.URLField(db_column="picture_url")

    class Meta:
        db_table = "post_picture"


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
    userId = models.IntegerField(db_column="user_id", primary_key=True)
    deviceId = models.CharField(max_length=255, db_column="device_id", null=True)
    token = models.CharField(max_length=255, db_column="user_token", null=True)
    nickname = models.CharField(max_length=255, db_column='nickname')
    telephone = models.CharField(max_length=50, db_column="telephone")
    avatar = models.CharField(max_length=255, db_column="avatar", null=True)
    sex = models.IntegerField(db_column="sex", choices=SEX_CHOICES, default=DEFAULT)
    birthday = models.DateField(db_column="birthday", null=True)
    sign = models.CharField(max_length=255, db_column="sign", null=True)
    schoolId = models.IntegerField(db_column="school_id", null=True)

    class Meta:
        db_table = "user_info"

    def setattrs(self, data):
        modify = False
        for field in self._meta.fields:
            attr = field.name
            value = data.get(attr.lower())
            # 非空并不等才更新
            if value is not None and value != getattr(self, attr):
                if attr == 'telephone' and not utils.is_avaliable_phone(value):
                    continue
                setattr(self, attr, value)
                modify = True
        return modify

    def tojson(self):
        ret = {}
        for field in self._meta.fields:
            attr = field.name
            ret[attr] = getattr(self, attr)
        return ret


class FirstLevelReply(models.Model):
    postId = models.IntegerField(db_column="post_id", db_index=True)
    userId = models.IntegerField(db_column="user_id")
    content = models.CharField(db_column="content", max_length=800)
    upCount = models.IntegerField(db_column="up_count")
    replyCount = models.IntegerField(db_column="reply_count")
    replyUserCount = models.IntegerField(db_column="reply_user_count")
    floor = models.IntegerField(db_column="floor")
    replyTime = models.DateTimeField(db_column="create_time")
    score = models.FloatField(db_column="score")
    editStatus = models.IntegerField(db_column="edit_status")

    class Meta:
        db_table = "first_level_reply"

    def to_json(self, user):
        ret = {}
        for field in self._meta.fields:
            attr = field.name
            if attr == 'id':
                ret['firstLevelReplyId'] = getattr(self, attr)
            elif attr == "userId":
                ret['user'] = user
            else:
                ret[attr] = getattr(self, attr)
        return ret


class SecondLevelReply(models.Model):
    postId = models.IntegerField(db_column="post_id", db_index=True)
    firstLevelReplyId = models.IntegerField(db_column="first_level_reply_id", db_index=True)
    userId = models.IntegerField(db_column="user_id")
    content = models.CharField(db_column="content", max_length=140)
    replyTime = models.DateTimeField(db_column="create_time")
    editStatus = models.IntegerField(db_column="edit_status")

    class Meta:
        db_table = "second_level_reply"

    def to_json(self, user):
        ret = {}
        for field in self._meta.fields:
            attr = field.name
            if attr == 'id':
                ret['secondLevelReplyId'] = getattr(self, attr)
            elif attr == "userId":
                ret['user'] = user
            else:
                ret[attr] = getattr(self, attr)
        return ret


class UpPost(models.Model):
    postId = models.IntegerField(db_column="post_id", primary_key=True)
    userId = models.IntegerField(db_column="user_id")

    class Meta:
        db_table = "up_post"


class ReplyPost(models.Model):
    postId = models.IntegerField(db_column="post_id", primary_key=True)
    userId = models.IntegerField(db_column="user_id")

    class Meta:
        db_table = "reply_post"


class OpposePost(models.Model):
    postId = models.IntegerField(db_column="post_id", primary_key=True)
    userId = models.IntegerField(db_column="user_id")

    class Meta:
        db_table = "oppose_post"


class UpReply(models.Model):
    postId = models.IntegerField(db_column="post_id", primary_key=True)
    firstLevelReplyId = models.IntegerField(db_column="first_level_reply_id", db_index=True)
    userId = models.IntegerField(db_column="user_id")

    class Meta:
        db_table = "up_reply"


class ReplyReply(models.Model):
    postId = models.IntegerField(db_column="post_id", primary_key=True)
    firstLevelReplyId = models.IntegerField(db_column="first_level_reply_id", db_index=True)
    userId = models.IntegerField(db_column="user_id")

    class Meta:
        db_table = "reply_reply"
