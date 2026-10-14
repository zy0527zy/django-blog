"""djangoblog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.urls import re_path
from haystack.views import search_view_factory
from django.http import JsonResponse
import time

from blog.views import EsSearchView
from djangoblog.admin_site import admin_site
from djangoblog.elasticsearch_backend import ElasticSearchModelSearchForm
from djangoblog.feeds import DjangoBlogFeed
from djangoblog.sitemap import ArticleSiteMap, CategorySiteMap, StaticViewSitemap, TagSiteMap, UserSiteMap

# 站点地图配置：把各模型映射为站点地图类，供 /sitemap.xml 使用（利于搜索引擎收录）
sitemaps = {

    'blog': ArticleSiteMap,
    'Category': CategorySiteMap,
    'Tag': TagSiteMap,
    'User': UserSiteMap,
    'static': StaticViewSitemap
}

# 自定义错误页视图：404 页面不存在 / 500 服务器错误 / 403 无权限
handler404 = 'blog.views.page_not_found_view'
handler500 = 'blog.views.server_error_view'
handle403 = 'blog.views.permission_denied_view'


def health_check(request):
    """
    健康检查接口
    简单返回服务健康状态
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': time.time()
    })

# ==================== 全局路由表 ====================
# 作用：把"URL 模式"映射到"视图或子路由"，决定一个请求该由哪个 app 的哪个视图处理（请求怎么被路由）。
#  - path()/re_path() 定义一条路由规则，re_path 支持正则表达式
#  - include('xxx.urls', namespace='yyy') 把某个 app 的 URL 挂到全局路由里，并用 namespace 命名，
#    方便在模板/视图中用 'yyy:name' 反向解析出真实 URL（例如 blog:index）
#  - 下面绝大部分业务路由都用 i18n_patterns 包裹，会自动加上语言前缀（如 /zh-hans/...）
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),          # 语言切换接口
    path('health/', health_check, name='health_check'),       # 健康检查接口
]
# i18n_patterns：为内部路由统一加语言前缀并做国际化处理；
# prefix_default_language=False 表示默认语言（中文）不带前缀，其它语言才带前缀
urlpatterns += i18n_patterns(
    re_path(r'^admin/', admin_site.urls),                                     # 后台管理
    re_path(r'', include('blog.urls', namespace='blog')),                     # 博客：文章/分类/标签等
    re_path(r'mdeditor/', include('mdeditor.urls')),                          # Markdown 编辑器（图片上传等）
    re_path(r'', include('comments.urls', namespace='comment')),              # 评论
    re_path(r'', include('accounts.urls', namespace='account')),              # 账号：登录/注册/个人中心
    re_path(r'', include('oauth.urls', namespace='oauth')),                   # 第三方 OAuth 登录
    re_path(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps},
            name='django.contrib.sitemaps.views.sitemap'),                    # 站点地图
    re_path(r'^feed/$', DjangoBlogFeed()),                                    # RSS 订阅（Atom）
    re_path(r'^rss/$', DjangoBlogFeed()),                                     # RSS 订阅（别名）
    re_path('^search', search_view_factory(view_class=EsSearchView, form_class=ElasticSearchModelSearchForm),
            name='search'),                                                   # 全文搜索
    re_path(r'', include('servermanager.urls', namespace='servermanager'))    # 服务器管理
    , prefix_default_language=False) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# static()：把 /static/ 映射到 STATIC_ROOT 目录，直接伺服静态文件（CSS/JS/图片等）
if settings.DEBUG:
    # 仅调试模式（runserver）下额外伺服 /media/ 上传文件；生产环境由 Nginx 等服务器处理
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
