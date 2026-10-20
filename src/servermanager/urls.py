from django.urls import path
from werobot.contrib.django import make_view

from .robot import robot
"""
servermanager应用urls路由配置文件
功能：定义本应用所有对外访问的接口路由，当前仅配置微信机器人消息回调地址
"""
#zly: 应用命名空间。
app_name = "servermanager"
#zly: 路由匹配列表，存放当前应用全部 URL 与视图映射关系。
"""路由匹配列表，存放当前应用全部url与视图映射关系"""
urlpatterns = [
    #zly: 微信公众平台服务器配置的回调地址；make_view 把 WeRoBot 实例包装成 Django 视图。
    path(r'robot', make_view(robot)),

]
