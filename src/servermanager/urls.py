#zly: 模块说明：servermanager 的 URL 路由配置，当前仅暴露微信机器人回调地址。
"""
servermanager应用urls路由配置文件
功能：定义本应用所有对外访问的接口路由，当前仅配置微信机器人消息回调地址
"""
from django.urls import path
from werobot.contrib.django import make_view

from .robot import robot

#zly: 应用命名空间（Django 约定小写，Pylint 的常量命名规则不适用）。
app_name = "servermanager"  # pylint: disable=invalid-name
#zly: 路由匹配列表，存放当前应用全部 URL 与视图映射关系。
urlpatterns = [
    #zly: 微信公众平台服务器配置的回调地址；make_view 把 WeRoBot 实例包装成 Django 视图。
    path(r'robot', make_view(robot)),

]
