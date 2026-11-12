"""
第九、十周：文章本周阅读量与热门文章测试。
负责人：黄梓涵。
"""

from datetime import datetime, timedelta

from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils import timezone

from blog.models import Article, ArticleWeeklyView
from blog.templatetags.blog_tags import (
    get_weekly_hot_articles,
    load_sidebar,
)
from djangoblog.test_base import BaseTestCase


class WeeklyViewsTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        cache.clear()

    def test_weekly_counter_created(self):
        #hzh: 阅读后同时产生累计和本周计数。
        self.article.viewed()
        self.article.refresh_from_db()

        self.assertEqual(self.article.views, 1)

        record = ArticleWeeklyView.objects.get(
            article=self.article
        )
        self.assertEqual(record.views, 1)
        self.assertEqual(record.week_start.weekday(), 0)

    def test_multiple_views_same_week(self):
        #hzh: 同一周的阅读次数应当累加。
        for _ in range(3):
            self.article.viewed()

        self.article.refresh_from_db()
        self.assertEqual(self.article.views, 3)

        records = ArticleWeeklyView.objects.filter(
            article=self.article
        )
        self.assertEqual(records.count(), 1)
        self.assertEqual(records.first().views, 3)

    def test_existing_total_not_used_as_weekly(self):
        #hzh: 历史累计次数不能冒充本周次数。
        Article.objects.filter(pk=self.article.pk).update(
            views=100
        )

        self.article.viewed()
        self.article.refresh_from_db()

        self.assertEqual(self.article.views, 101)

        record = ArticleWeeklyView.objects.get(
            article=self.article
        )
        self.assertEqual(record.views, 1)

    def test_previous_week_excluded(self):
        #hzh: 上周阅读记录不进入本周排行。
        today = datetime.now(timezone.get_current_timezone()).date()
        monday = today - timedelta(days=today.weekday())

        ArticleWeeklyView.objects.create(
            article=self.article,
            week_start=monday - timedelta(days=7),
            views=100
        )

        self.assertEqual(get_weekly_hot_articles(), [])

    def test_rank_uses_weekly_views(self):
        #hzh: 本周热门不能按历史累计阅读量排序。
        other = self.create_article(
            title="本周阅读量更高的文章"
        )

        Article.objects.filter(pk=self.article.pk).update(
            views=1000
        )

        self.article.viewed()

        for _ in range(3):
            other.viewed()

        ranked = get_weekly_hot_articles()

        self.assertEqual(ranked[0].pk, other.pk)
        self.assertEqual(ranked[0].weekly_views, 3)
        self.assertEqual(ranked[1].pk, self.article.pk)
        self.assertEqual(ranked[1].weekly_views, 1)

    def test_draft_and_page_excluded(self):
        #hzh: 本周热门只展示已发布普通文章。
        draft = self.create_article(
            title="本周草稿",
            status="d"
        )
        page = self.create_article(
            title="本周独立页面",
            article_type="p"
        )

        draft.viewed()
        page.viewed()
        self.article.viewed()

        ranked = get_weekly_hot_articles()

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].pk, self.article.pk)

    def test_sidebar_cache_refreshes_weekly(self):
        #hzh: 旧侧栏缓存不能冻结本周阅读量排行。
        before = load_sidebar(self.user, "i")
        self.assertEqual(before["weekly_hot_articles"], [])

        self.article.viewed()

        after = load_sidebar(self.user, "i")

        self.assertEqual(
            after["weekly_hot_articles"][0].pk,
            self.article.pk
        )

    def test_sidebar_template_renders_weekly(self):
        #hzh: 页面应正确展示本周热门标题和次数。
        self.article.viewed()

        context = load_sidebar(self.user, "i")
        rendered = render_to_string(
            "blog/tags/sidebar.html",
            context
        )

        self.assertIn("本周热门文章", rendered)
        self.assertIn(self.article.title, rendered)
        self.assertIn("本周 1 次阅读", rendered)


    def test_total_hot_updates_after_views(self):
        #hzh: 旧侧栏缓存不应导致累计热门长期显示旧数据。
        other = self.create_article(
            title="累计热门缓存刷新测试"
        )

        self.article.viewed()

        before = load_sidebar(self.user, "i")
        self.assertEqual(
            before["most_read_articles"][0].pk,
            self.article.pk
        )

        other.viewed()
        other.viewed()

        after = load_sidebar(self.user, "i")

        self.assertEqual(
            after["most_read_articles"][0].pk,
            other.pk
        )
        self.assertEqual(
            after["most_read_articles"][0].views,
            2
        )

    def test_index_cache_invalidated_after_view(self):
        #hzh: 阅读量增加后，首页第一页的缓存应失效。
        cache.set('index_1', 'old_article_list')

        self.article.viewed()

        self.assertIsNone(cache.get('index_1'))


    def test_existing_plugin_still_counts(self):
        #hzh: 复用原有阅读量插件入口。
        from plugins.view_count.plugin import ViewCountPlugin

        ViewCountPlugin().record_view(self.article)

        self.article.refresh_from_db()

        self.assertEqual(self.article.views, 1)
        self.assertEqual(
            ArticleWeeklyView.objects.get(
                article=self.article
            ).views,
            1
        )
