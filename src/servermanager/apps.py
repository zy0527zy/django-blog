#zly: 模块说明：servermanager 的 Django AppConfig 配置，用于定义当前 App 的基础配置。
from django.apps import AppConfig  #zly: 导入 Django 应用配置基类

#zly: ServermanagerConfig：servermanager 应用的配置类，继承 AppConfig。
class ServermanagerConfig(AppConfig):
    name = 'servermanager'  #zly: 指定应用名称，Django 通过该名称识别 App。
