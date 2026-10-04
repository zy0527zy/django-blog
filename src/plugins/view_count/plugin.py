"""
文章浏览次数统计插件主文件
监听文章内容读取后的钩子事件，调用文章模型viewed方法完成浏览量自增。
"""
from djangoblog.plugin_manage.base_plugin import BasePlugin
from djangoblog.plugin_manage import hooks


class ViewCountPlugin(BasePlugin):
    """文章浏览次数统计插件类，实现文章访问计数"""
    PLUGIN_NAME = '文章浏览次数统计'
    PLUGIN_DESCRIPTION = '统计文章的浏览次数'
    PLUGIN_VERSION = '0.1.0'
    PLUGIN_AUTHOR = 'liangliangyy'

    def register_hooks(self):
        """注册钩子：在获取文章主体内容之后触发统计函数"""
        hooks.register('after_article_body_get', self.record_view)

    def record_view(self, article, *args, **kwargs):
        """
        记录文章访问，调用模型方法增加浏览数
        :param article: 当前访问的文章实例
        """
        article.viewed()


plugin = ViewCountPlugin()
