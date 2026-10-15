# =============================================================================
# comments 应用 · 测试用例（tests.py）
# -----------------------------------------------------------------------------
# 本文件是 Django 自动发现的测试文件之一，测试评论模块的核心业务逻辑：
#   - 评论的创建与展示审核（is_enable）
#   - 楼中楼回复（parent_comment 自关联）
#   - 评论正文的 Markdown 渲染与自定义模板标签（parse_commenttree）
# 运行：python manage.py test comments
# =============================================================================
from django.test import Client, RequestFactory, TransactionTestCase
from django.urls import reverse

from accounts.models import BlogUser
from blog.models import Category, Article
from comments.models import Comment
from comments.templatetags.comments_tags import *
from djangoblog.utils import get_max_articleid_commentid


# Create your tests here.

class CommentsTest(TransactionTestCase):
    """评论模块的核心业务逻辑测试。"""

    def setUp(self):
        """准备测试环境：客户端、测试数据，并开启评论审核开关。"""
        self.client = Client()
        self.factory = RequestFactory()
        from blog.models import BlogSettings
        # 开启评论审核，用于验证"发表后需审核才展示"的流程
        value = BlogSettings()
        value.comment_need_review = True
        value.save()

        # 创建一个超级用户作为测试作者
        self.user = BlogUser.objects.create_superuser(
            email="liangliangyy1@gmail.com",
            username="liangliangyy1",
            password="liangliangyy1")

    def update_article_comment_status(self, article):
        """辅助方法：把某篇文章的所有评论设为已展示（is_enable=True）。"""
        comments = article.comment_set.all()
        for comment in comments:
            comment.is_enable = True
            comment.save()

    def test_validate_comment(self):
        """核心用例：评论创建、审核展示、楼中楼回复、模板标签全链路。"""
        # 登录用户后创建一篇文章
        self.client.login(username='liangliangyy1', password='liangliangyy1')

        category = Category()
        category.name = "categoryccc"
        category.save()

        article = Article()
        article.title = "nicetitleccc"
        article.body = "nicecontentccc"
        article.author = self.user
        article.category = category
        article.type = 'a'
        article.status = 'p'
        article.save()

        # 提交评论（POST 到 postcomment 路由）
        comment_url = reverse(
            'comments:postcomment', kwargs={
                'article_id': article.id})

        response = self.client.post(comment_url,
                                    {
                                        'body': '123ffffffffff'
                                    })

        # 评论提交成功，302 重定向回文章页
        self.assertEqual(response.status_code, 302)

        # 因开启审核，此时评论未展示，文章评论数为 0
        article = Article.objects.get(pk=article.pk)
        self.assertEqual(len(article.comment_list()), 0)
        self.update_article_comment_status(article)

        # 审核通过后评论展示，数量变为 1
        self.assertEqual(len(article.comment_list()), 1)

        response = self.client.post(comment_url,
                                    {
                                        'body': '123ffffffffff',
                                    })

        self.assertEqual(response.status_code, 302)

        # 第二条评论同样审核后展示，数量变为 2
        article = Article.objects.get(pk=article.pk)
        self.update_article_comment_status(article)
        self.assertEqual(len(article.comment_list()), 2)
        parent_comment_id = article.comment_list()[0].id

        # 第三条：带 parent_comment_id 的楼中楼回复（正文为 Markdown 语法）
        response = self.client.post(comment_url,
                                    {
                                        'body': '''
                                        # Title1

        ```python
        import os
        ```

        [url](https://www.lylinux.net/)

        [ddd](http://www.baidu.com)


        ''',
                                        'parent_comment_id': parent_comment_id
                                    })

        self.assertEqual(response.status_code, 302)
        self.update_article_comment_status(article)
        article = Article.objects.get(pk=article.pk)
        self.assertEqual(len(article.comment_list()), 3)

        # 验证 parse_commenttree 能正确取到父评论的子评论（楼中楼）
        comment = Comment.objects.get(id=parent_comment_id)
        tree = parse_commenttree(article.comment_list(), comment)
        self.assertEqual(len(tree), 1)

        # 验证 show_comment_item 模板标签可用
        data = show_comment_item(comment, True)
        self.assertIsNotNone(data)

        # 验证工具函数可用
        s = get_max_articleid_commentid()
        self.assertIsNotNone(s)

        # 验证评论邮件通知可正常调用
        from comments.utils import send_comment_email
        send_comment_email(comment)
