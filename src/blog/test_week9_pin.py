"""
第九、十周：文章置顶与取消置顶自动化测试。
负责人：黄梓涵。
"""

#hzh: 测试后台置顶、取消置顶、文章排序、权限和缓存更新。
from django.core.cache import cache
from django.urls import reverse

from blog.models import Article
from djangoblog.test_base import BaseTestCase


class ArticlePinTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse("admin:blog_article_changelist")
        self.client.force_login(self.admin_user)

    def test_pin_button_visible(self):
        """后台列表应该显示置顶按钮。"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'name="pin_article_id"'
        )

    def test_single_pin(self):
        """单篇文章可以置顶。"""
        response = self.client.post(
            self.url,
            {"pin_article_id": self.article.pk}
        )

        self.assertEqual(response.status_code, 302)

        self.article.refresh_from_db()
        self.assertGreater(self.article.article_order, 0)

    def test_single_unpin(self):
        """已经置顶的文章可以取消置顶。"""
        self.client.post(
            self.url,
            {"pin_article_id": self.article.pk}
        )

        self.client.post(
            self.url,
            {"unpin_article_id": self.article.pk}
        )

        self.article.refresh_from_db()
        self.assertEqual(self.article.article_order, 0)

    def test_pin_button_changes_to_unpin(self):
        """置顶后后台按钮应变为取消置顶。"""
        self.client.post(
            self.url,
            {"pin_article_id": self.article.pk}
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'name="unpin_article_id"'
        )

    def test_pinned_article_first(self):
        """置顶文章应该排列在普通文章之前。"""
        other = self.create_article(
            title="第九周普通文章"
        )

        self.client.post(
            self.url,
            {"pin_article_id": self.article.pk}
        )

        articles = list(
            Article.objects.filter(status="p")
        )

        self.assertEqual(articles[0].pk, self.article.pk)
        self.assertEqual(other.article_order, 0)

    def test_batch_pin_and_unpin(self):
        """批量置顶和取消置顶。"""
        other = self.create_article(
            title="第九周批量测试文章"
        )

        ids = [
            str(self.article.pk),
            str(other.pk)
        ]

        response = self.client.post(
            self.url,
            {
                "action": "pin_articles",
                "index": "0",
                "_selected_action": ids
            }
        )

        self.assertEqual(response.status_code, 302)

        self.article.refresh_from_db()
        other.refresh_from_db()

        self.assertGreater(self.article.article_order, 0)
        self.assertGreater(other.article_order, 0)

        response = self.client.post(
            self.url,
            {
                "action": "unpin_articles",
                "index": "0",
                "_selected_action": ids
            }
        )

        self.assertEqual(response.status_code, 302)

        self.article.refresh_from_db()
        other.refresh_from_db()

        self.assertEqual(self.article.article_order, 0)
        self.assertEqual(other.article_order, 0)

    def test_get_request_cannot_pin(self):
        """GET 请求不能修改文章置顶状态。"""
        self.client.get(
            self.url,
            {"pin_article_id": self.article.pk}
        )

        self.article.refresh_from_db()
        self.assertEqual(self.article.article_order, 0)

    def test_normal_user_cannot_pin(self):
        """普通用户不能执行后台置顶。"""
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {"pin_article_id": self.article.pk}
        )

        self.assertIn(response.status_code, [302, 403])

        self.article.refresh_from_db()
        self.assertEqual(self.article.article_order, 0)

    def test_cache_invalidated(self):
        """置顶后旧文章列表缓存应该失效。"""
        cache.set("index_1", "old_article_list")

        self.client.post(
            self.url,
            {"pin_article_id": self.article.pk}
        )

        self.assertIsNone(cache.get("index_1"))
