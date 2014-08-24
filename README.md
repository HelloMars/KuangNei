KuangNei
========

`http://kuangnei.me/`

## Setup ##
* `git clone git@github.com:HelloMars/KuangNei.git` #从github克隆代码
* `virtualenv KuangNei` #创建虚拟python环境
* `source KuangNei/bin/activate` #启动虚拟环境
* (pip freeze > requirements.txt 命令保存了所需包的版本)
* `pip install Django` (1.6.5) #虚拟环境下装Django
* `pip install uwsgi` (2.0.6)
* `pip install mysql-python` (1.2.5) #mysql drive
* `pip install qiniu` (6.1.8)
* `pip install fabric` (可选，用于自动化部署)
* `cd KuangNei`
* `python manage.py collectstatic`
* `python manage.py syncdb` #输入admin账户密码
* `cp uwsgi.ini.template uwsgi.ini` 并修改相应配置
* `cp mysql.cnf.template mysql.cnf` 并修改对应数据库配置
* `sh run.sh` 启动uwsgi，自动加载python文件，daemonize=log/uwsgi.log
* `kill -INT {pid}` 停止uwsgi
* `fab update` git pull, syncdb, unit test...

## API ##
### returned json ###

* 所有API会返回json来传输数据，所有json数据都包含`returnCode`和`returnMessage`两个字段表明调用情况
* returnCode
    * 0: success
    * 1: incorrect parameters
    * 2: incorrect request method [GET, POST]
    * 10: user system error
    * 11: incorrect format of parameters

### API List ###
1. `[GET] http://kuangnei.me/kuangnei/api/getUpToken/`, 获得图片上传token，【需要登陆】
    * 返回json示例
    ```
    {
        uptoken: "qZUvN3pdML7x0pa4LPoP2iLI5iif0DP1l5JLx1Ax:6J_cbPoJEV8pqoFXgZRBQ9SiFKk=:eyJzY29wZSI6Imt1YW5nbmVpIiwiZGVhZGxpbmUiOjE0MDgyOTExODV9",
        returnMessage: "",
        returnCode: 0
    }
    ```
2. `[GET] http://kuangnei.me/kuangnei/api/getDnUrl/?key={image_name}`, 获得私有空间图片下载url，【需要登陆】
    * 返回json示例
    ```
    {
        dnurl: "http://kuangnei.qiniudn.com/image.jpg?e=1408291300&token=qZUvN3pdML7x0pa4LPoP2iLI5iif0DP1l5JLx1Ax:isuiw6VSBaeAQXh9D2R3kWRIBuA=",
        returnMessage: "",
        returnCode: 0
    }
        ```
3. `[POST] http://kuangnei.me/kuangnei/api/post/`, 发帖子，【需要登陆】
    * POST请求必要参数: `{'channelid': 1, 'content': 'test, 测试中文'}`, 可选参数: `{imageurl: 'url1@url2@url3'}`
    * 返回json:
    ```
    {
        "returnMessage": "",
        "returnCode": 0,
        "postId": 4
    }
    ```
4. `[GET] http://kuangnei.me/kuangnei/api/postlist/?channelid=1&page=1`, 拉取帖子列表，【需要登陆】
    * page表明第几批数据（目前后端一批有五个帖子）
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
                "content": "test, 测试中文",
                "upCount": 0,
                "user": {
                    "id": 1,
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
5. `[POST] https://kuangnei.me/kuangnei/api/register/`, 注册
    * POST请求必要参数: 
    ```
        {
         'username': '18910690027', # username必须为合法手机号
         'password': '123456',
         'token': 'xxx'
        }
    ```
    * 返回json:
    ```
       {
        "returnMessage": "",
        "returnCode": 0,
        "user": "18910690027"
       }
    ```
6. `[POST] https://kuangnei.me/kuangnei/api/signin/`, 登录
    * POST请求必要参数:
    ```
        {
         'username': '18910690027', # username必须为合法手机号
         'password': '123456',
        }
    ```
    * POST请求可选参数: `{'token': 'xxx'}` 用于更新个推clientID
    * 返回json:
    ```    
      {
       "returnMessage": "登陆成功",
        "returnCode": 0,
      }
    ```
7. `[GET] https://kuangnei.me/kuangnei/api/logout/`, 退出
    * 返回json:
    ```    
      {
       "returnMessage": "退出成功",
        "returnCode": 0,
      }
    ```
8. `[POST] http://kuangnei.me/kuangnei/api/checkIfUserExist/` 查看用户是否存在
    * POST请求必要参数: `{'username': '18910690027'}`
    * 返回json:
    ```
        {
        "returnMessage": "",
        "returnCode": 0,
        "exist": True
       }
    ```
9. `[POST] http://kuangnei.me/kuangnei/api/addUserInfo/` 添加/修改/查询用户信息，【需要登陆】
    * POST请求可选参数:
    ```
        个推token (可修改，非null，注册时写入)
        昵称nickname, (可修改，非null，注册时默认'user'+userId)
        电话telephone, (可修改，非null，注册时默认等于username)
        头像avatar, (可修改，可null)
        性别sex, (可修改，int，默认3 {0:female, 1:male, 2:neutral, 3:未设置}) 
        生日birthday, (可修改，可null)
        签名sign, (可修改，可null)
        学校schoolId, (可修改，可null，int)
    ```
    * POST请求没有任何参数时返回查询用户信息结果
    * 返回json:
    ```
        {
            "returnMessage": "获取个人信息成功",
            "returnCode": 0,
            "id": 1
            "userId": 1,
            "token": "xxx",
            "nickname": "user1",
            "telephone": "18910690027",
            "avatar": null,
            "sex": 3,
            "birthday": null,
            "sign": null,
            "schoolId": null,
        }
    ```
10. `[GET] http://kuangnei.me/kuangnei/api/channellist/`, 频道列表，【需要登陆】
    * 返回json:
    ```
    {
        returnMessage: "",
        returnCode: 0,
        list: [
            {
                subtitle: "不有趣可能会被踢得很惨哦",
                id: 0,
                title: "兴趣"
            },
            {
                subtitle: "约会、表白、同性异性不限",
                id: 1,
                title: "缘分"
            }
        ],
        size: 2
    }
    ```
11. `[GET] http://kuangnei.me/kuangnei/api/postdetail/?postId=1&page=1`, 帖子详细，【需要登陆】
    * 返回json:
    ```
    {
    }
    ```
12. `[POST] http://kuangnei.me/kuangnei/api/replyFirstLevel/`, 一级回复，【需要登陆】
    * POST请求必要参数: `{'postId': 1, 'content': '一级回复'}`
    * 返回json:
    ```
    {
    }
    ```
13. `[POST] http://kuangnei.me/kuangnei/api/replySecondLevel/`, 二级回复，【需要登陆】
    * POST请求必要参数: `{'firstLevelId': 1, 'content': '一级回复'}`
    * 返回json:
    ```
    {
    }
    ```
14. `[GET] http://kuangnei.me/kuangnei/api/replydetail/?firstLevelId=1&page=1`, 一级回复详细，【需要登陆】
    * 返回json:
    ```
    {
    }
    ```
15. `[POST] http://kuangnei.me/kuangnei/api/uppost/`, 赞帖子，【需要登陆】
    * POST请求必要参数: `{'postId': 1}`
    * 返回json:
    ```
    {
    }
    ```
16. `[POST] http://kuangnei.me/kuangnei/api/upreply/`, 赞一级回复，【需要登陆】
    * POST请求必要参数: `{'firstLevelId': 1}`
    * 返回json:
    ```
    {
    }
    ```
17. `[POST] http://kuangnei.me/kuangnei/api/opposepost/`, 踩帖子，【需要登陆】
    * POST请求必要参数: `{'postId': 1}`
    * 返回json:
    ```
    {
    }
    ```

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
