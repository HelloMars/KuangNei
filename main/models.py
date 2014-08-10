# -*- coding: utf-8 -*-
from django.db import models
from datetime import datetime
import json

# Create your models here.


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

class Choice(models.Model):
    question = models.ForeignKey(Question)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    
class Post(models.Model):
    userId = models.CharField(max_length=255,db_column = "user_id")
    schoolId = models.IntegerField(db_column ="school_id")
    content = models.CharField(max_length=800)
    channel = models.IntegerField()
    opposedCount = models.IntegerField(db_column ="unlike_count")
    upCount = models.IntegerField(db_column ="like_count")
    postTime = models.DateTimeField('date published',db_column ="create_time")  
    replyCount = models.IntegerField(db_column ="back_count")
    currentFloor = models.IntegerField(db_column ="current_floor")
    rank = models.IntegerField()
    editStatus = models.IntegerField(db_column ="edit_status")
    class Meta:
        db_table = "post"
    def toJSON(self,imageurl,user):
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime) else json.JSONEncoder().default(obj)
        fields = []
        for field in self._meta.fields:
            fields.append(field.name)
        d = {}
        for attr in fields:
            if(attr == "id"):
                d['postId'] = getattr(self,attr)
            elif(attr == "userId"):
                d['user'] = user
            else:
                d[attr] = getattr(self, attr)
        d['pictures'] = imageurl
        return json.dumps(d, default=dthandler)
 
    
class Post_picture(models.Model):
    post_id = models.BigIntegerField()
    picture_url = models.URLField()
    create_time = models.DateTimeField()
    picture_size = models.CharField(max_length=255)
    class Meta:
        db_table = "post_picture"
