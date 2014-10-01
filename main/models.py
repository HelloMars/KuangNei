# -*- coding: utf-8 -*-
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


class Post(models.Model):
    #userId = models.IntegerField(db_column="user_id")
    user = models.ForeignKey(User)
    schoolId = models.IntegerField(db_column="school_id")
    content = models.CharField(max_length=800)
    channelId = models.IntegerField(db_column="channel_id")
    opposedCount = models.IntegerField(db_column="opposed_count")
    upCount = models.IntegerField(db_column="up_count")
    postTime = models.DateTimeField('date published', db_column="create_time")
    replyCount = models.IntegerField(db_column="reply_count")
    replyUserCount = models.IntegerField(db_column="reply_user_count")
    score = models.FloatField(db_column="score")
    imageUrls = models.CharField(db_column="image_urls", max_length=1000)
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
    user = models.ForeignKey(User)
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
            #生日由long转化为时间类型
            if attr == "birthday" and value is not None:
                print value
                value = datetime.fromtimestamp((long(value))/1e3)
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
            if attr == "user":
                user = getattr(self, "user")
                ret["user"] = user.id
            else:
                ret[attr] = getattr(self, attr)
        return ret


class FirstLevelReply(models.Model):
    #postId = models.IntegerField(db_column="post_id", db_index=True)
    post = models.ForeignKey(Post)
    #userId = models.IntegerField(db_column="user_id")
    user = models.ForeignKey(User)
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
            if attr == 'post':
                ret['postId'] = self.post.id
            elif attr == "user":
                ret['user'] = user
            else:
                ret[attr] = getattr(self, attr)
        return ret


class SecondLevelReply(models.Model):
    #postId = models.IntegerField(db_column="post_id", db_index=True)
    #firstLevelReplyId = models.IntegerField(db_column="first_level_reply_id", db_index=True)
    #userId = models.IntegerField(db_column="user_id")
    post = models.ForeignKey(Post)
    first_level_reply = models.ForeignKey(FirstLevelReply)
    secondLevelReplyId = models.IntegerField(db_column="second_level_reply_id", default=0)
    user = models.ForeignKey(User)
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
            elif attr == 'post':
                ret['postId'] = self.post.id
            elif attr == 'first_level_reply':
                ret['firstLevelReplyId'] = self.first_level_reply.id
            elif attr == "user":
                ret['user'] = user
            else:
                ret[attr] = getattr(self, attr)
        return ret


class UpPost(models.Model):
    postId = models.IntegerField(db_column="post_id")
    userId = models.IntegerField(db_column="user_id")

    class Meta:
        db_table = "up_post"
        unique_together = ("postId", "userId")


class ReplyPost(models.Model):
    postId = models.IntegerField(db_column="post_id")
    userId = models.IntegerField(db_column="user_id")

    class Meta:
        db_table = "reply_post"
        unique_together = ("postId", "userId")


class OpposePost(models.Model):
    postId = models.IntegerField(db_column="post_id")
    userId = models.IntegerField(db_column="user_id")

    class Meta:
        db_table = "oppose_post"
        unique_together = ("postId", "userId")


class UpReply(models.Model):
    postId = models.IntegerField(db_column="post_id")
    firstLevelReplyId = models.IntegerField(db_column="first_level_reply_id", db_index=True)
    userId = models.IntegerField(db_column="user_id")

    class Meta:
        db_table = "up_reply"
        unique_together = ("firstLevelReplyId", "userId")


class ReplyReply(models.Model):
    postId = models.IntegerField(db_column="post_id")
    firstLevelReplyId = models.IntegerField(db_column="first_level_reply_id", db_index=True)
    userId = models.IntegerField(db_column="user_id")

    class Meta:
        db_table = "reply_reply"
        unique_together = ("firstLevelReplyId", "userId")


class ReplyInfo(models.Model):
    repliedUser = models.ForeignKey(User,related_name='replied_user')  #被回复人
    replyUser = models.ForeignKey(User,related_name='reply_user')   #回复人
    flag = models.IntegerField()  #1代表是对帖子的回复，2代表是对一级回复的回复，3代表对二级回复的回复
    repliedBriefContent = models.CharField(db_column="replied_brief_content", max_length=50)  #我的发表的内容，缩略
    replyContent = models.CharField(db_column="reply_content", max_length=800)                 #对我的回复
    postId = models.IntegerField(db_column="post_id")
    firstLevelReplyId = models.IntegerField(db_column="first_level_reply_id", default=0)
    secondLevelReplyId = models.IntegerField(db_column="second_level_reply_id", default=0)
    replyTime = models.DateTimeField(db_column="reply_time")

    class Meta:
        db_table = "reply_info"

    def to_json(self, user):
        ret = {}
        for field in self._meta.fields:
            attr = field.name
            if attr == "replyUser":
                pass
            elif attr == "repliedUser":
                pass
            else:
                ret[attr] = getattr(self, attr)
                ret['showUser'] = user                           #showUser字段用来显示消息列表中……的帖子或回复
        return ret

