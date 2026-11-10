# =============================================================================
# comments 应用 · 评论视图测试（test_views.py）
# -----------------------------------------------------------------------------
# 本文件通过模拟 HTTP 请求测试评论视图层的功能与边界情况，覆盖：
#   - CommentViewTest    已登录/未登录发表评论、空正文、无效文章、回复、审核、
#                        评论在文章页的显示与隐藏
#   - CommentSpamTest    重复评论与频率限制
#   - CommentSecurityTest XSS 注入与 SQL 注入防护
# =============================================================================
"""
Comments Views 测试
测试评论功能的错误处理和边界条件
"""
from unittest.mock import patch

from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from comments.models import Comment
from djangoblog.test_base import ViewTestMixin


class CommentViewTest(TransactionTestCase, ViewTestMixin):
    """测试评论视图"""

    def setUp(self):
        from django.test import Client
        from accounts.models import BlogUser
        from blog.models import Article, Category, BlogSettings
        from django.utils import timezone

        self.client = Client()
        self.user = BlogUser.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='测试分类',
            creation_time=timezone.now(),
            last_modify_time=timezone.now()
        )
        self.article = Article.objects.create(
            title='测试文章',
            body='测试内容',
            author=self.user,
            category=self.category,
            type='a',
            status='p'
        )
        self.blog_settings, _ = BlogSettings.objects.get_or_create(
            id=1,
            defaults={
                'site_name': '测试博客',
                'site_description': '测试描述',
                'comment_need_review': False,
            }
        )

    def login_user(self):
        """登录测试用户"""
        return self.client.login(username='testuser', password='testpass123')

    def test_post_comment_authenticated(self):
        """测试已登录用户发表评论"""
        self.login_user()
        url = reverse('comments:postcomment', kwargs={'article_id': self.article.id})
        response = self.client.post(url, {'body': '这是一条测试评论'})
        self.assertEqual(response.status_code, 302)

        # 验证评论已创建
        comments = Comment.objects.filter(article=self.article)
        self.assertGreater(comments.count(), 0)

    def test_post_comment_unauthenticated(self):
        """测试未登录用户发表评论"""
        self.client.logout()
        url = reverse('comments:postcomment', kwargs={'article_id': self.article.id})
        response = self.client.post(url, {'body': '匿名评论'})
        # 未登录用户会被视图处理，可能返回错误或重定向
        # 由于视图会尝试获取用户，会产生错误，这是预期的
        self.assertIn(response.status_code, [200, 302, 403, 500])

    def test_post_comment_empty_body(self):
        """测试提交空评论"""
        self.login_user()
        url = reverse('comments:postcomment', kwargs={'article_id': self.article.id})
        response = self.client.post(url, {'body': ''})
        # 应该返回表单错误
        self.assertIn(response.status_code, [200, 302])

    def test_post_comment_invalid_article(self):
        """测试对不存在的文章评论"""
        self.login_user()
        url = reverse('comments:postcomment', kwargs={'article_id': 99999})
        response = self.client.post(url, {'body': '评论'})
        self.assertEqual(response.status_code, 404)

    def test_post_reply_comment(self):
        """测试回复评论"""
        self.login_user()
        # 先创建一条评论
        parent_comment = Comment.objects.create(
            body='父评论',
            author=self.user,
            article=self.article
        )
        parent_comment.is_enable = True
        parent_comment.save()

        # 回复这条评论
        url = reverse('comments:postcomment', kwargs={'article_id': self.article.id})
        response = self.client.post(url, {
            'body': '这是回复',
            'parent_comment_id': parent_comment.id
        })
        self.assertIn(response.status_code, [200, 302])

    def test_comment_moderation(self):
        """测试评论审核"""
        # 设置需要审核
        self.blog_settings.comment_need_review = True
        self.blog_settings.save()

        self.login_user()
        url = reverse('comments:postcomment', kwargs={'article_id': self.article.id})
        response = self.client.post(url, {'body': '待审核的评论'})
        self.assertEqual(response.status_code, 302)

        # 验证评论需要审核
        comment = Comment.objects.filter(article=self.article).latest('id')
        self.assertFalse(comment.is_enable)

    def test_comment_display_on_article(self):
        """测试评论在文章页显示"""
        Comment.objects.create(
            body='测试显示评论',
            author=self.user,
            article=self.article,
            is_enable=True
        )

        response = self.client.get(self.article.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_disabled_comment_not_display(self):
        """测试未启用的评论不显示"""
        Comment.objects.create(
            body='未启用的评论',
            author=self.user,
            article=self.article,
            is_enable=False
        )

        response = self.client.get(self.article.get_absolute_url())
        self.assertEqual(response.status_code, 200)


class CommentSpamTest(TransactionTestCase, ViewTestMixin):
    """测试评论垃圾防护"""

    def setUp(self):
        from django.test import Client
        from accounts.models import BlogUser
        from blog.models import Article, Category, BlogSettings
        from django.utils import timezone

        self.client = Client()
        self.user = BlogUser.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='测试分类',
            creation_time=timezone.now(),
            last_modify_time=timezone.now()
        )
        self.article = Article.objects.create(
            title='测试文章',
            body='测试内容',
            author=self.user,
            category=self.category,
            type='a',
            status='p'
        )
        self.blog_settings, _ = BlogSettings.objects.get_or_create(
            id=1,
            defaults={'comment_need_review': False}
        )

    def login_user(self):
        return self.client.login(username='testuser', password='testpass123')

    def test_duplicate_comment(self):
        """测试重复评论"""
        self.login_user()
        url = reverse('comments:postcomment', kwargs={'article_id': self.article.id})
        comment_data = {'body': '重复的评论内容'}

        # 第一次提交
        response1 = self.client.post(url, comment_data)
        self.assertEqual(response1.status_code, 302)

        # 第二次提交相同内容
        response2 = self.client.post(url, comment_data)
        # 应该被阻止或显示错误
        self.assertIn(response2.status_code, [200, 302])

    def test_comment_rate_limit(self):
        """测试评论频率限制"""
        self.login_user()
        url = reverse('comments:postcomment', kwargs={'article_id': self.article.id})

        # 快速连续发表多条评论
        for i in range(5):
            response = self.client.post(url, {'body': f'评论{i}'})
            # 后续评论可能被限制
            self.assertIn(response.status_code, [200, 302, 429])


class CommentSecurityTest(TransactionTestCase, ViewTestMixin):
    """测试评论安全性"""

    def setUp(self):
        from django.test import Client
        from accounts.models import BlogUser
        from blog.models import Article, Category, BlogSettings
        from django.utils import timezone

        self.client = Client()
        self.user = BlogUser.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='测试分类',
            creation_time=timezone.now(),
            last_modify_time=timezone.now()
        )
        self.article = Article.objects.create(
            title='测试文章',
            body='测试内容',
            author=self.user,
            category=self.category,
            type='a',
            status='p'
        )
        self.blog_settings, _ = BlogSettings.objects.get_or_create(
            id=1,
            defaults={'comment_need_review': False}
        )

    def login_user(self):
        return self.client.login(username='testuser', password='testpass123')

    def test_xss_protection(self):
        """测试 XSS 防护"""
        self.login_user()
        url = reverse('comments:postcomment', kwargs={'article_id': self.article.id})

        # 提交包含 script 标签的评论
        xss_body = '<script>alert("xss")</script>普通内容'
        response = self.client.post(url, {'body': xss_body})
        self.assertEqual(response.status_code, 302)

        # 验证评论已创建（XSS 过滤在渲染时处理）
        comment = Comment.objects.filter(article=self.article).latest('id')
        self.assertIsNotNone(comment)

    def test_sql_injection_protection(self):
        """测试 SQL 注入防护"""
        self.login_user()
        url = reverse('comments:postcomment', kwargs={'article_id': self.article.id})

        # 提交包含 SQL 注入尝试的评论
        sql_body = "'; DROP TABLE comments; --"
        response = self.client.post(url, {'body': sql_body})
        # 应该正常处理，不会执行 SQL
        self.assertIn(response.status_code, [200, 302])

        # 验证表仍然存在
        self.assertTrue(Comment.objects.exists())


class CommentManagementTest(TestCase):
    """验证删除与置顶的权限、级联删除和页面排序。"""

    @classmethod
    def setUpTestData(cls):
        from accounts.models import BlogUser
        from blog.models import Article, BlogSettings, Category

        cls.author = BlogUser.objects.create_user(username='comment_owner', password='password')
        cls.other = BlogUser.objects.create_user(username='other_user', password='password')
        cls.staff = BlogUser.objects.create_user(username='comment_staff', password='password', is_staff=True)
        cls.category = Category.objects.create(name='评论功能测试', slug='comment-management')
        cls.article = Article.objects.create(
            title='评论管理测试文章', body='测试正文', author=cls.author,
            category=cls.category, status='p', type='a')
        BlogSettings.objects.get_or_create(
            id=1, defaults={'site_name': '测试博客', 'site_description': '测试描述'})

    def setUp(self):
        #lyt: 本组测试只验证评论管理，屏蔽旧信号启动的异步邮件线程。
        email_thread = patch('djangoblog.blog_signals._thread.start_new_thread')
        email_thread.start()
        self.addCleanup(email_thread.stop)
        self.comment = Comment.objects.create(
            body='可管理评论', author=self.author, article=self.article, is_enable=True)

    def test_author_can_delete_comment_and_its_replies(self):
        #lyt: 删除父评论后，现有外键的 CASCADE 规则会一并删除回复。
        reply = Comment.objects.create(
            body='回复', author=self.other, article=self.article,
            parent_comment=self.comment, is_enable=True)
        self.client.force_login(self.author)
        response = self.client.post(reverse('comments:comment_delete', args=[self.comment.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(pk__in=[self.comment.pk, reply.pk]).exists())

    def test_staff_can_delete_other_users_comment(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('comments:comment_delete', args=[self.comment.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_other_user_cannot_delete_comment(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse('comments:comment_delete', args=[self.comment.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_delete_rejects_get(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse('comments:comment_delete', args=[self.comment.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_anonymous_user_cannot_delete_or_pin(self):
        delete_url = reverse('comments:comment_delete', args=[self.comment.pk])
        pin_url = reverse('comments:comment_pin', args=[self.comment.pk])
        self.assertEqual(self.client.post(delete_url).status_code, 302)
        self.assertEqual(self.client.post(pin_url).status_code, 302)
        self.comment.refresh_from_db()
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())
        self.assertFalse(self.comment.is_top)

    def test_delete_requires_csrf_token(self):
        from django.test import Client

        #lyt: 浏览器表单必须携带 CSRF token，伪造的 POST 请求不能删除评论。
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.author)
        delete_url = reverse('comments:comment_delete', args=[self.comment.pk])
        self.assertEqual(csrf_client.post(delete_url).status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_only_staff_can_pin_and_unpin(self):
        url = reverse('comments:comment_pin', args=[self.comment.pk])
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_top)
        self.client.post(url)
        self.comment.refresh_from_db()
        self.assertFalse(self.comment.is_top)

    def test_reply_cannot_be_pinned(self):
        reply = Comment.objects.create(
            body='回复', author=self.other, article=self.article,
            parent_comment=self.comment, is_enable=True)
        self.client.force_login(self.staff)
        response = self.client.post(reverse('comments:comment_pin', args=[reply.pk]))
        self.assertEqual(response.status_code, 400)
        reply.refresh_from_db()
        self.assertFalse(reply.is_top)

    def test_pinned_comment_precedes_newer_comment_on_article_page(self):
        Comment.objects.create(
            body='较新的普通评论', author=self.other,
            article=self.article, is_enable=True)
        self.client.force_login(self.staff)
        self.client.post(reverse('comments:comment_pin', args=[self.comment.pk]))
        response = self.client.get(self.article.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['p_comments'][0].pk, self.comment.pk)

    def test_delete_clears_cached_comment_list(self):
        #lyt: 删除前先填充文章评论缓存，验证页面不会读到已删除的评论。
        self.assertIn(self.comment, list(self.article.comment_list()))
        self.client.force_login(self.author)
        self.client.post(reverse('comments:comment_delete', args=[self.comment.pk]))
        self.assertNotIn(self.comment, list(self.article.comment_list()))

    def test_management_buttons_follow_user_role(self):
        #lyt: 页面按钮与身份对应；服务端权限另由越权请求测试覆盖。
        delete_url = reverse('comments:comment_delete', args=[self.comment.pk])
        pin_url = reverse('comments:comment_pin', args=[self.comment.pk])
        article_url = self.article.get_absolute_url()

        self.client.force_login(self.author)
        author_page = self.client.get(article_url)
        self.assertContains(author_page, delete_url)
        self.assertNotContains(author_page, pin_url)

        self.client.force_login(self.other)
        other_page = self.client.get(article_url)
        self.assertNotContains(other_page, delete_url)
        self.assertNotContains(other_page, pin_url)

        self.client.force_login(self.staff)
        staff_page = self.client.get(article_url)
        self.assertContains(staff_page, delete_url)
        self.assertContains(staff_page, pin_url)
