"""oauth 应用的 AppConfig，定义 oauth 应用的 Django 配置。"""
#xcz: 定义 OAuth 应用配置，供 Django 加载第三方登录功能。

from django.apps import AppConfig


#xcz: 为 Django 提供 OAuth 应用的名称和加载配置。
class OauthConfig(AppConfig):
    """第三方 OAuth 登录应用的配置类。"""

    # 应用的完整 Python 路径，Django 通过它定位到 oauth 包
    name = 'oauth'
