#zy: 模块精读：插件加载器。load_plugins() 遍历 settings.ACTIVE_PLUGINS，用 __import__ 动态导入各插件的 plugin 模块并收集实例；
#zy: 在 apps.py 的 ready() 里被调用（Django 应用就绪后），是"运行时动态加载插件"而非标准 app 注册的核心。
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# 全局插件注册表
_loaded_plugins = []

def load_plugins():
    """
    Dynamically loads and initializes plugins from the 'plugins' directory.
    This function is intended to be called when the Django app registry is ready.
    """
    global _loaded_plugins
    _loaded_plugins = []

    for plugin_name in settings.ACTIVE_PLUGINS:
        plugin_path = os.path.join(settings.PLUGINS_DIR, plugin_name)
        if os.path.isdir(plugin_path) and os.path.exists(os.path.join(plugin_path, 'plugin.py')):
            try:
                # 导入插件模块
                plugin_module = __import__(f'plugins.{plugin_name}.plugin', fromlist=['plugin'])

                # 获取插件实例
                if hasattr(plugin_module, 'plugin'):
                    plugin_instance = plugin_module.plugin
                    _loaded_plugins.append(plugin_instance)
                    logger.info(f"Successfully loaded plugin: {plugin_name} - {plugin_instance.PLUGIN_NAME}")
                else:
                    logger.warning(f"Plugin {plugin_name} does not have 'plugin' instance")

            except ImportError as e:
                logger.error(f"Failed to import plugin: {plugin_name}", exc_info=e)
            except AttributeError as e:
                logger.error(f"Failed to get plugin instance: {plugin_name}", exc_info=e)
            except Exception as e:
                logger.error(f"Unexpected error loading plugin: {plugin_name}", exc_info=e)

    return _loaded_plugins

def get_loaded_plugins():
    """获取所有已加载的插件"""
    return _loaded_plugins

def get_plugin_by_name(plugin_name):
    """根据名称获取插件"""
    for plugin in _loaded_plugins:
        if plugin.plugin_slug == plugin_name:
            return plugin
    return None

def get_plugin_by_slug(plugin_slug):
    """根据slug获取插件"""
    for plugin in _loaded_plugins:
        if plugin.plugin_slug == plugin_slug:
            return plugin
    return None

def get_plugins_info():
    """获取所有插件的信息"""
    return [plugin.get_plugin_info() for plugin in _loaded_plugins]

def get_plugins_by_position(position):
    """获取支持指定位置的插件"""
    return [plugin for plugin in _loaded_plugins if position in plugin.SUPPORTED_POSITIONS] 