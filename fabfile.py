from fabric.api import lcd, local
import os

def update():
    if not os.path.exists('log'):
        os.mkdir('log')
    local('git pull')
    local('python manage.py syncdb')
    local('python manage.py test')
