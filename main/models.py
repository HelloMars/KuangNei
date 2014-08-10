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
    user_id = models.CharField(max_length=255)
    school_id = models.IntegerField()
    content = models.CharField(max_length=800)
    channel = models.IntegerField()
    unlike_count = models.IntegerField()
    create_time = models.DateTimeField('date published')  
    back_count = models.IntegerField()
    current_floor = models.IntegerField()
    rank = models.IntegerField()
    edit_status = models.IntegerField()
    class Meta:
        db_table = "post"
    def toJSON(self,imageurl):
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime) else json.JSONEncoder().default(obj)
        fields = []
        for field in self._meta.fields:
            fields.append(field.name)
        d = {}
        for attr in fields:
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
