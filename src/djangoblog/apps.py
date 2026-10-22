#zy: 模块精读：应用配置类 DjangoblogAppConfig。关键点在 ready()——Django 应用注册表就绪后自动加载 plugins 目录下已启用的插件，
#zy: 这是本项目"插件系统"的启动入口（自定义扩展，非 Django 标准能力）。
from django.apps import AppConfig


class DjangoblogAppConfig(AppConfig):
    """djangoblog 应用配置：在 Django 应用注册表就绪时自动加载插件。"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'djangoblog'

    def ready(self):
        """Django 启动、应用注册表就绪后的回调，用于加载 plugins 目录下已启用的插件。"""
        super().ready()
        # 导入并加载所有已启用插件（读取 settings.ACTIVE_PLUGINS 配置）
        from .plugin_manage.loader import load_plugins
        load_plugins()
