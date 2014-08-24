from django.conf.urls import patterns, include, url

from main import views

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/', views.rlogin_in, name='rlogin'),
    url(r'.*kuangnei/api/', include('main.urls')),
)
