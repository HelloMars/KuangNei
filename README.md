KuangNei
========

`http://kuangnei.me/`

## Setup ##
* `git clone git@github.com:HelloMars/KuangNei.git` #从github克隆代码
* `virtualenv KuangNei` #创建虚拟python环境
* `source KuangNei/bin/activate` #启动虚拟环境
* `pip install Django` (1.6.5) #虚拟环境下装Django
* `pip install uwsgi` (2.0.6)
* `pip install mysql-python` (1.2.5) #mysql drive
* `pip install qiniu` (6.1.8)
* `cd KuangNei`
* `python manage.py collectstatic`
* `python manage.py syncdb` #输入admin账户密码
* `cp uwsgi.ini.template uwsgi.ini` 并修改相应配置
* `uwsgi --py-auto-reload=3 --ini uwsgi.ini` 启动uwsgi，3s自动加载python文件

## API ##
### returned json ###

* 所有API会返回json来传输数据，所有json数据都包含`returnCode`和`returnMessage`两个字段表明调用情况
* returnCode
    * 0: success
    * 1: incorrect parameters

### API List ###
* qiniu
    * `[GET] http://kuangnei.me/kuangnei/api/getUpToken/`, 获得图片上传token
        * 返回json示例
        ```
        {
            uptoken: "qZUvN3pdML7x0pa4LPoP2iLI5iif0DP1l5JLx1Ax:6J_cbPoJEV8pqoFXgZRBQ9SiFKk=:eyJzY29wZSI6Imt1YW5nbmVpIiwiZGVhZGxpbmUiOjE0MDgyOTExODV9",
            returnMessage: "",
            returnCode: 0
        }
        ```
    * `[GET] http://kuangnei.me/kuangnei/api/getDnUrl/?key={image_name}`, 获得私有空间图片下载url
        * 返回json示例
        ```
        {
            dnurl: "http://kuangnei.qiniudn.com/image.jpg?e=1408291300&token=qZUvN3pdML7x0pa4LPoP2iLI5iif0DP1l5JLx1Ax:isuiw6VSBaeAQXh9D2R3kWRIBuA=",
            returnMessage: "",
            returnCode: 0
        }
        ```
* `[POST] http://kuangnei.me/kuangnei/api/post/`, 发帖子
    * POST请求必要参数: `{'userid': 1, 'channelid': 1, 'content': 'test, 测试中文'}`, 可选参数: `{imageurl: 'url1@url2@url3'}`
    * 返回json:
    ```
    {
        "returnMessage": "",
        "returnCode": 0,
        "postId": 4
    }
    ```
* `[GET] http://kuangnei.me/kuangnei/api/postlist/?userid=1&channelid=1&page=1`, 拉取帖子列表
    * page表明第几批数据（目前后端一批有五个帖子）
    * 返回json:
* channel list: `[GET] http://kuangnei.me/kuangnei/api/channellist/`
    * 返回json:
    ```
    {
        "returnMessage": "",
        "returnCode": 0,
        "list": [
            {
                "editStatus": 0,
                "postTime": "2014-08-17 23:03:10",
                "currentFloor": 1,
                "schoolId": 1,
                "pictures": [],
                "channelId": 1,
                "postId": 4,
                "replyCount": 0,
                "content": "test",
                "upCount": 0,
                "user": {
                    "id": "1",
                    "name": "框内",
                    "avatar": "http://kuangnei.qiniudn.com/FjMgIjdmHH9lkUm9Ra_K1VbKynxR"
                },
                "rank": 1,
                "opposedCount": 0
            },
        ],
        "size": 1
    }
    ```
* 

## Log ##
后端log采用python自带的logging模块，以天为节点输出在`log/debug_YYYY_mm_dd.log`文件。在自己的python文件使用该模块示例：
```
from kuangnei.utils import logger

logger.debug("debug")
logger.info("info")
logger.warn("warn")
logger.error("error")
```
linux下通过 `tail -f log/debug_YYYY_mm_dd.log` 来观察log变化


## Unit Test ##
框内针对每个API都有单元测试，修改API以后需要执行：
`python manage.py test`
确保所有测试通过再提交代码

## MySql ##

## Git管理 ##