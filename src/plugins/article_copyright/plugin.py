"""
文章版权插件主文件
功能：在文章正文末尾追加版权声明，摘要模式下不添加版权信息
"""
from djangoblog.plugin_manage.base_plugin import BasePlugin
from djangoblog.plugin_manage import hooks
from djangoblog.plugin_manage.hook_constants import ARTICLE_CONTENT_HOOK_NAME


class ArticleCopyrightPlugin(BasePlugin):
    """文章版权插件类，继承基础插件类，实现文章内容钩子注册"""
    PLUGIN_NAME = '文章结尾版权声明'
    PLUGIN_DESCRIPTION = '一个在文章正文末尾添加版权声明的插件。'
    PLUGIN_VERSION = '0.2.0'
    PLUGIN_AUTHOR = 'liangliangyy'

    # 2. 实现 register_hooks 方法，专门用于注册钩子
    def register_hooks(self):
        """注册钩子函数，将版权添加方法挂载到文章内容钩子"""
        # 在这里将插件的方法注册到指定的钩子上
        hooks.register(ARTICLE_CONTENT_HOOK_NAME, self.add_copyright_to_content)

    def add_copyright_to_content(self, content, *args, **kwargs):
        """
        给文章内容追加版权信息
        这个方法会被注册到 'the_content' 过滤器钩子上。
        它接收原始内容，并返回添加了版权信息的新内容。
        :param content: 文章原始html内容
        :param args: 可变位置参数
        :param kwargs: 关键字参数，包含article、is_summary
        :return: 拼接版权信息后的文章内容
        """
        article = kwargs.get('article')
        if not article:
            return content
        
        # 如果是摘要模式（首页），不添加版权声明
        is_summary = kwargs.get('is_summary', False)
        if is_summary:
            return content

        copyright_info = f"\n<hr><p>本文由 {article.author.username} 原创，转载请注明出处。</p>"
        return content + copyright_info


# 3. 实例化插件。
# 这会自动调用 BasePlugin.__init__，然后 BasePlugin.__init__ 会调用我们上面定义的 register_hooks 方法。
plugin = ArticleCopyrightPlugin()
