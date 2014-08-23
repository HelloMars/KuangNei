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
    userId = models.CharField(max_length=255, db_column="user_id")
    schoolId = models.IntegerField(db_column="school_id")
    content = models.CharField(max_length=800)
    channelId = models.IntegerField(db_column="channel")
    opposedCount = models.IntegerField(db_column="unlike_count")
    upCount = models.IntegerField(db_column="like_count")
    postTime = models.DateTimeField('date published', db_column="create_time")
    replyCount = models.IntegerField(db_column="back_count")
    currentFloor = models.IntegerField(db_column="current_floor")
    rank = models.IntegerField()
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


class Post_picture(models.Model):
    post_id = models.BigIntegerField()
    picture_url = models.URLField()
    create_time = models.DateTimeField()
    picture_size = models.CharField(max_length=255)

    class Meta:
        db_table = "post_picture"


class UserInfo(models.Model):
    FEMALE = 0
    MALE = 1
    NEUTRAL = 2
    SEX_CHOICES = (
        (FEMALE, 'Female'),
        (MALE, 'Male'),
        (NEUTRAL, 'Neutral'),
        (3, 'Null')
    )
    userId = models.IntegerField(db_column="user_id")
    token = models.CharField(max_length=255, db_column="user_token")
    nickname = models.CharField(max_length=255, db_column='nickname')
    telephone = models.CharField(max_length=50, db_column="telephone")
    avatar = models.CharField(max_length=255, db_column="avatar", null=True)
    sex = models.IntegerField(db_column="sex", choices=SEX_CHOICES, default=3)
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
            if value is not None:
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


class PostResponse(models.Model):
    postId = models.IntegerField(db_column="post_id", db_index=True)
    userId = models.IntegerField(db_column="user_id")
    content = models.CharField(db_column="content", max_length=500)
    floor = models.IntegerField(db_column="floor")
    createTime = models.DateTimeField(db_column="create_time")
    editStatus = models.IntegerField(db_column="edit_status")

    class Meta:
        db_table = "post_response"
