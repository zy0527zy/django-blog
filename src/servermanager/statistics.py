#zly: 模块说明：servermanager 站点数据统计服务，集中聚合各业务模型的数据，供统计面板视图调用。
"""
src/servermanager/statistics.py

站点数据统计服务：
把分散在 blog / comments / accounts / oauth / servermanager 中的统计数据
集中到一个服务类里查询，避免视图层堆砌 ORM 代码，也方便单独测试。
"""
from datetime import timedelta

from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from accounts.models import BlogUser
from blog.models import Article, Category, Tag
from comments.models import Comment
from oauth.models import OAuthUser

from .models import EmailSendLog


#zly: SiteStatisticsService：聚合站点核心指标（文章 / 评论 / 用户 / 分类标签 / 邮件）。
class SiteStatisticsService:
    """站点数据统计服务：一次查询返回统计面板所需的全部指标。"""

    #zly: 热门文章只取前 5 篇，避免面板过长。
    TOP_ARTICLE_LIMIT = 5
    #zly: 最近失败邮件只取前 5 条，用于快速排查。
    RECENT_FAILED_EMAIL_LIMIT = 5

    #zly: collect：汇总文章、评论、用户、分类标签、近 7 天与邮件发送数据。
    def collect(self):
        """汇总站点统计数据并返回字典。"""
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        article_qs = Article.objects.all()
        comment_qs = Comment.objects.all()
        email_qs = EmailSendLog.objects.all()

        #zly: 邮件成功率单独算好，模板里直接展示百分比。
        email_total = email_qs.count()
        email_success = email_qs.filter(send_result=True).count()
        email_failed = email_total - email_success

        return {
            #zly: 文章相关：总数、已发布、草稿、阅读量总和、近 7 天新增。
            'article_total': article_qs.count(),
            'article_published': article_qs.filter(status='p').count(),
            'article_draft': article_qs.filter(status='d').count(),
            'article_views': article_qs.aggregate(
                total=Coalesce(Sum('views'), 0))['total'],
            'article_week': article_qs.filter(pub_time__gte=week_ago).count(),
            #zly: 评论相关：总数、待审核数、近 7 天新增。
            'comment_total': comment_qs.count(),
            'comment_pending': comment_qs.filter(is_enable=False).count(),
            'comment_week': comment_qs.filter(
                creation_time__gte=week_ago).count(),
            #zly: 用户相关：站点用户与第三方登录用户。
            'user_total': BlogUser.objects.count(),
            'oauth_user_total': OAuthUser.objects.count(),
            #zly: 分类与标签数量。
            'category_total': Category.objects.count(),
            'tag_total': Tag.objects.count(),
            #zly: 邮件发送：总数、成功、失败、成功率。
            'email_total': email_total,
            'email_success': email_success,
            'email_failed': email_failed,
            'email_success_rate': (
                round(email_success * 100 / email_total, 1) if email_total else 0),
            #zly: 热门文章 Top5：只统计已发布文章，按阅读量倒序。
            'top_articles': list(
                article_qs.filter(status='p').order_by('-views')[
                    :self.TOP_ARTICLE_LIMIT]),
            #zly: 最近失败邮件：按创建时间倒序，展示失败原因。
            'recent_failed_emails': list(
                email_qs.filter(send_result=False).order_by('-creation_time')[
                    :self.RECENT_FAILED_EMAIL_LIMIT]),
        }
