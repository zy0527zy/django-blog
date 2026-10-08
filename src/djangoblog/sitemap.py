"""
djangoblog sitemap.py 文件
功能：定义站点地图（Sitemap）各数据源
把首页、文章、分类、标签、用户等页面映射为 sitemap.xml，利于搜索引擎收录
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blog.models import Article, Category, Tag


# 静态页面站点地图：收录固定路由（首页等）
class StaticViewSitemap(Sitemap):
    priority = 0.5          # 页面优先级
    changefreq = 'daily'    # 更新频率：每天

    def items(self):
        """返回需要收录的静态路由名列表"""
        return ['blog:index', ]

    def location(self, item):
        """根据路由名反向解析出真实 URL"""
        return reverse(item)


# 文章站点地图：收录所有已发布的文章
class ArticleSiteMap(Sitemap):
    changefreq = "monthly"  # 更新频率：每月
    priority = "0.6"        # 优先级

    def items(self):
        """返回所有已发布文章"""
        return Article.objects.filter(status='p')

    def lastmod(self, obj):
        """返回文章最后修改时间（供搜索引擎判断是否需要重新抓取）"""
        return obj.last_modify_time


# 分类站点地图：收录所有分类页
class CategorySiteMap(Sitemap):
    changefreq = "Weekly"
    priority = "0.6"

    def items(self):
        """返回所有分类"""
        return Category.objects.all()

    def lastmod(self, obj):
        """返回分类最后修改时间"""
        return obj.last_modify_time


# 标签站点地图：收录所有标签页
class TagSiteMap(Sitemap):
    changefreq = "Weekly"
    priority = "0.3"

    def items(self):
        """返回所有标签"""
        return Tag.objects.all()

    def lastmod(self, obj):
        """返回标签最后修改时间"""
        return obj.last_modify_time


# 用户站点地图：收录所有文章作者（去重）
class UserSiteMap(Sitemap):
    changefreq = "Weekly"
    priority = "0.3"

    def items(self):
        """返回所有文章的去重作者列表"""
        return list(set(map(lambda x: x.author, Article.objects.all())))

    def lastmod(self, obj):
        """返回用户注册时间"""
        return obj.date_joined
