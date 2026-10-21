"""oauth 应用的 AppConfig，定义 oauth 应用的 Django 配置。"""

from django.apps import AppConfig


class OauthConfig(AppConfig):
    """第三方 OAuth 登录应用的配置类。"""

    # 应用的完整 Python 路径，Django 通过它定位到 oauth 包
    name = 'oauth'
