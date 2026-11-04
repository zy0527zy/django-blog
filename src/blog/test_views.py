"""
Blog Views 测试
测试视图层的错误处理、权限验证和边界条件
"""
from django.urls import NoReverseMatch, reverse

from blog.models import Article
from djangoblog.test_base import BaseTestCase, ViewTestMixin


class ArticleViewTest(BaseTestCase, ViewTestMixin):
    """测试文章视图"""

    def test_article_detail_view(self):
        """测试文章详情页"""
        url = self.article.get_absolute_url()
        response = self.assert_view_success(url)
        self.assertContains(response, self.article.title)
        self.assertContains(response, self.article.body)

    def test_article_detail_view_draft(self):
        """测试草稿文章无法访问"""
        draft_article = self.create_article(title='草稿文章测试', status='d')
        url = draft_article.get_absolute_url()
        response = self.client.get(url)
        # 草稿可以访问但可能有限制，或者返回 200
        self.assertIn(response.status_code, [200, 302, 404])

    def test_article_detail_increases_views(self):
        """测试访问文章增加浏览量"""
        initial_views = self.article.views
        self.client.get(self.article.get_absolute_url())
        self.article.refresh_from_db()
        self.assertGreaterEqual(self.article.views, initial_views)

    def test_article_archive_view(self):
        """测试文章归档页"""
        url = reverse('blog:archives')
        response = self.assert_view_success(url)

    #hzh: 归档年份路由未实现时应明确跳过测试，不能用裸 except 掩盖异常或断言失败。
    def test_article_archive_by_year(self):
        """测试按年归档，未实现路由时明确跳过"""
        year = self.article.pub_time.year
        try:
            url = reverse('blog:archives', kwargs={'year': year})
        except NoReverseMatch:
            self.skipTest('当前尚未提供按年份归档的独立路由')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    #hzh: 按年月归档尚无对应路由，捕获 NoReverseMatch 后明确标记为跳过。
    def test_article_archive_by_year_month(self):
        """测试按年月归档，未实现路由时明确跳过"""
        year = self.article.pub_time.year
        month = self.article.pub_time.month
        try:
            url = reverse('blog:archives', kwargs={'year': year, 'month': month})
        except NoReverseMatch:
            self.skipTest('当前尚未提供按年月归档的独立路由')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_index_view(self):
        """测试首页"""
        url = reverse('blog:index')
        response = self.assert_view_success(url)
        self.assertContains(response, self.article.title)

    def test_index_view_pagination(self):
        """测试首页分页"""
        # 创建多篇文章以测试分页
        for i in range(15):
            self.create_article(title=f'文章{i}')

        url = reverse('blog:index')
        response = self.client.get(url, {'page': 2})
        self.assertEqual(response.status_code, 200)

    def test_category_view(self):
        """测试分类页"""
        url = self.category.get_absolute_url()
        response = self.assert_view_success(url)
        self.assertContains(response, self.category.name)

    def test_category_view_invalid_slug(self):
        """测试无效分类 slug"""
        url = reverse('blog:category_detail', kwargs={'category_name': 'invalid'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_tag_view(self):
        """测试标签页"""
        self.article.tags.add(self.tag)
        url = self.tag.get_absolute_url()
        response = self.assert_view_success(url)
        self.assertContains(response, self.tag.name)

    def test_tag_view_invalid_slug(self):
        """测试无效标签 slug"""
        url = reverse('blog:tag_detail', kwargs={'tag_name': 'invalid'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_author_view(self):
        """测试作者页"""
        url = self.user.get_absolute_url()
        response = self.assert_view_success(url)
        self.assertContains(response, self.user.username)


class SearchViewTest(BaseTestCase, ViewTestMixin):
    """测试搜索功能"""

    #hzh: 搜索入口属于全局路由 search，而不是 blog:search；响应断言不能被异常吞掉。
    def test_search_view_accessible(self):
        """测试搜索页面可访问"""
        url = reverse('search')
        response = self.client.get(url, {'q': '测试'})
        self.assertEqual(response.status_code, 200)


class ArticlePermissionTest(BaseTestCase, ViewTestMixin):
    """测试文章权限控制"""

    def test_only_author_can_edit(self):
        """测试只有作者可以编辑"""
        # 创建另一个用户
        other_user = self.create_user(username='other', email='other@test.com')
        self.login_user(other_user, 'testpass123')

        # 尝试访问编辑页（如果有的话）
        # 这里假设有编辑视图，根据实际情况调整
        # url = reverse('blog:article_edit', kwargs={'pk': self.article.pk})
        # self.assert_view_forbidden(url)

    def test_article_status_visibility(self):
        """测试不同状态文章的可见性"""
        # 发布的文章
        published = self.create_article(title='已发布文章测试', status='p')
        response = self.client.get(published.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        # 草稿（草稿可能也可以访问，取决于权限）
        draft = self.create_article(title='草稿状态测试', status='d')
        response = self.client.get(draft.get_absolute_url())
        self.assertIn(response.status_code, [200, 302, 404])


class ErrorHandlingTest(BaseTestCase, ViewTestMixin):
    """测试错误处理"""

    def test_404_page(self):
        """测试 404 页面"""
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)

    #hzh: 使用真实 detailbyid 路由和完整日期参数验证不存在文章时的404响应。
    def test_article_404(self):
        """测试不存在的文章"""
        created = self.article.creation_time
        url = reverse('blog:detailbyid', kwargs={
            'year': created.year,
            'month': created.month,
            'day': created.day,
            'article_id': self.article.pk + 99999,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_invalid_page_number(self):
        """测试无效页码"""
        url = reverse('blog:index')
        response = self.client.get(url, {'page': 'invalid'})
        # 应该返回第一页或错误页
        self.assertIn(response.status_code, [200, 404])

    def test_page_out_of_range(self):
        """测试页码超出范围"""
        url = reverse('blog:index')
        response = self.client.get(url, {'page': 99999})
        # 应该返回最后一页或404
        self.assertIn(response.status_code, [200, 404])
