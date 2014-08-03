KuangNei
========

`http://kuangnei.me/`

## Setup ##
* `git clone git@github.com:HelloMars/KuangNei.git` #从github克隆代码
* `virtualenv KuangNei` #创建虚拟python环境
* `source KuangNei/bin/activate` #启动虚拟环境
* `pip install Django` #虚拟环境下装Django
* `pip install uwsgi`
* `pip install mysql-python` #mysql drive
* `cd KuangNei`
* `python manage.py collectstatic`
* `python manage.py syncdb` #输入admin账户密码
* `cp uwsgi.ini.template uwsgi.ini` 并修改相应配置
* `uwsgi --ini uwsgi.ini` 启动uwsgi

## API ##
* get post list: `http://kuangnei.me/kuangnei/api/postlist/`
* get category: `http://kuangnei.me/kuangnei/api/category/`
* 推送所有用户消息: `http://kuangnei.me/kuangnei/api/pushMessageToApp/`