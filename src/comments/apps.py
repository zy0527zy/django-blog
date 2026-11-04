# =============================================================================
# comments 应用 · 应用配置（apps.py）
# -----------------------------------------------------------------------------
# Django 通过 AppConfig 管理应用的元信息。本文件把 comments 注册为一个 Django
# 应用，使项目在 INSTALLED_APPS 中能正确识别、加载它的模型、迁移、模板标签等。
# =============================================================================
from django.apps import AppConfig


class CommentsConfig(AppConfig):
    #lyt: Django 用此配置识别 comments 应用并加载其模型与迁移。  # noqa: E265
    # 应用名称，必须与 comments 目录名保持一致
    name = 'comments'
