"""oauth 应用的 AppConfig，负责应用级配置与启动初始化。"""

from django.apps import AppConfig


class OauthConfig(AppConfig):
    """第三方 OAuth 登录应用的配置类。"""

    # 应用的完整 Python 路径，Django 通过它定位到 oauth 包
    name = 'oauth'
