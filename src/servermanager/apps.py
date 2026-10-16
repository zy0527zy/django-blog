# servermanager/apps.py
# Django应用配置文件，用于定义当前App的基础配置信息
from django.apps import AppConfig # 导入Django应用配置基类

# servermanager应用的配置类，继承AppConfig
class ServermanagerConfig(AppConfig):
    name = 'servermanager' # 指定当前Django应用名称，Django通过该名称识别App
