"""
djangoblog admin_site.py 文件
功能：自定义 Django 后台管理站点（AdminSite）
统一把全站各 app 的模型注册到后台，集中控制后台标题、访问权限与各模型入口
"""
from django.contrib.admin import AdminSite
from django.contrib.admin.models import LogEntry
from django.contrib.sites.admin import SiteAdmin
from django.contrib.sites.models import Site

# 导入各业务 app 的后台管理配置与模型（各 app 的 admin.py 提供对应的 ModelAdmin 类）
from accounts.admin import *
from blog.admin import *
from blog.models import *
from comments.admin import *
from comments.models import *
from djangoblog.logentryadmin import LogEntryAdmin
from oauth.admin import *
from oauth.models import *
from servermanager.admin import *
from servermanager.models import *


# 自定义后台站点类：继承 Django 默认 AdminSite，定制站点标题与访问权限
class DjangoBlogAdminSite(AdminSite):
    # 后台页面顶部标题栏文字
    site_header = 'djangoblog administration'
    # 后台页面 <title> 标题
    site_title = 'djangoblog site admin'

    def __init__(self, name='admin'):
        """构造方法：初始化后台站点实例"""
        super().__init__(name)

    def has_permission(self, request):
        """权限校验：只允许超级用户（is_superuser）进入后台"""
        return request.user.is_superuser

    # def get_urls(self):
    #     # 注释掉的旧代码：曾用于自定义"刷新缓存"后台路由，现已停用
    #     urls = super().get_urls()
    #     ...


# 创建全局唯一的后台站点实例，供 urls.py 中的 admin 路由引用
admin_site = DjangoBlogAdminSite(name='admin')

# 把各 app 的模型（含对应的 ModelAdmin 配置）注册到后台
admin_site.register(Article, ArticlelAdmin)           # 博客文章
admin_site.register(Category, CategoryAdmin)          # 文章分类
admin_site.register(Tag, TagAdmin)                    # 文章标签
admin_site.register(Links, LinksAdmin)                # 友情链接
admin_site.register(SideBar, SideBarAdmin)            # 侧边栏
admin_site.register(BlogSettings, BlogSettingsAdmin)  # 博客全局配置

admin_site.register(commands, CommandsAdmin)          # 服务器管理命令
admin_site.register(EmailSendLog, EmailSendLogAdmin)  # 邮件发送日志

admin_site.register(BlogUser, BlogUserAdmin)          # 用户（自定义用户模型）

admin_site.register(Comment, CommentAdmin)            # 评论

admin_site.register(OAuthUser, OAuthUserAdmin)        # 第三方授权用户
admin_site.register(OAuthConfig, OAuthConfigAdmin)    # 第三方登录配置

admin_site.register(Site, SiteAdmin)                  # Django 站点（多站点框架）

admin_site.register(LogEntry, LogEntryAdmin)          # 后台操作日志
