#zly: 模块说明：servermanager 的自动化测试，覆盖微信机器人消息处理、文章检索与管理员命令执行。
# servermanager/tests.py
# Django单元测试文件，用于对servermanager模块的各类功能编写自动化测试用例
from unittest import mock  #zly: 导入 mock，用于模拟邮件发送成功/失败

from django.core.management import call_command  #zly: 导入 call_command，测试自定义管理命令
from django.test import Client, RequestFactory, TestCase  #zly: 导入 Django 测试相关工具类
from django.urls import reverse  #zly: 导入 reverse，用于反向解析统计面板地址
from werobot.messages.messages import TextMessage  #zly: 导入微信机器人文本消息实体

from accounts.models import BlogUser  #zly: 导入博客用户模型
from blog.models import Article, Category  #zly: 导入博客分类、文章模型
from comments.models import Comment  #zly: 导入评论模型，统计面板测试需要造数据
from servermanager.api.commonapi import ChatGPT  #zly: 导入 ChatGPT 接口类

from .models import EmailSendLog, commands  #zly: 导入邮件日志与命令数据表模型
from .robot import (  #zly: 导入消息处理器、命令处理器、文章搜索/分类/最新文章处理函数
    CommandHandler,
    MessageHandler,
    category,
    recents,
    search,
)
from .services import EmailService  #zly: 导入邮件发送服务，测试失败重试逻辑


#zly: 测试代码入口（原注释：Create your tests here.）。
# Create your tests here.
#zly: servermanager 模块测试类，继承 Django 测试基类 TestCase。
# servermanager模块测试类，继承Django测试基类TestCase
class ServerManagerTest(TestCase):
    #zly: 测试前置方法：每个测试方法执行前自动运行，初始化测试客户端、请求工厂。
    # 测试前置方法，每个测试方法执行前自动运行，初始化测试客户端、请求工厂
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

    #zly: 测试 ChatGPT 对话接口能否正常返回结果。
    # 测试ChatGPT对话接口能否正常返回结果
    def test_chat_gpt(self):
        content = ChatGPT.chat("你好")
        self.assertIsNotNone(content) #zly: 断言返回内容不为空

    #zly: 综合测试方法，测试微信机器人各类消息、命令、文章相关功能。
    # 综合测试方法，测试微信机器人各类消息、命令、文章相关功能
    def test_validate_comment(self):
        #zly: 创建超级管理员测试账号。
        # 创建超级管理员测试账号
        user = BlogUser.objects.create_superuser(
            email="liangliangyy1@gmail.com",
            username="liangliangyy1",
            password="liangliangyy1")
        self.client.login(username='liangliangyy1', password='liangliangyy1') #zly: 模拟登录管理员账号
        c = Category() #zly: 创建文章分类实例
        c.name = "categoryccc"
        c.save() #zly: 保存分类到测试数据库
        article = Article() #zly: 创建文章实例
        article.title = "nicetitleccc"
        article.body = "nicecontentccc"
        article.author = user
        article.category = c
        article.type = 'a'
        article.status = 'p'
        article.save() #zly: 保存文章到测试数据库
        s = TextMessage([]) #zly: 构造微信文本消息对象
        s.content = "nice"
        rsp = search(s, None) #zly: 调用文章搜索函数
        rsp = category(None, None) #zly: 调用分类查询函数
        self.assertIsNotNone(rsp) #zly: 断言返回结果不为空
        rsp = recents(None, None) #zly: 调用获取最新文章函数
        self.assertTrue(rsp != '暂时还没有文章') #zly: 断言存在文章数据
        cmd = commands() #zly: 创建命令记录实例
        cmd.title = "test"
        cmd.command = "ls"
        cmd.describe = "test"
        cmd.save() #zly: 保存测试命令
        cmdhandler = CommandHandler() #zly: 实例化命令处理器
        rsp = cmdhandler.run('test') #zly: 执行命令
        self.assertIsNotNone(rsp) #zly: 断言命令执行有返回
        s.source = 'u' #zly: 设置消息发送者标识
        s.content = 'test'
        msghandler = MessageHandler(s, {}) #zly: 实例化微信消息处理器
        # msghandler.userinfo.isPasswordSet = True
        # msghandler.userinfo.isAdmin = True
        msghandler.handler() #zly: 执行消息处理逻辑
        s.content = 'y'
        msghandler.handler() #zly: 处理 y 指令消息
        s.content = 'idcard:12321233'
        msghandler.handler() #zly: 处理身份证查询指令
        s.content = 'weather:上海'
        msghandler.handler() #zly: 处理天气查询指令
        s.content = 'admin'
        msghandler.handler() #zly: 处理管理员指令
        s.content = '123'
        msghandler.handler() #zly: 处理普通消息
        s.content = 'exit'
        msghandler.handler() #zly: 处理退出指令


#zly: 站点数据统计面板测试：覆盖权限控制与核心指标汇总。
class SiteStatisticsViewTest(TestCase):
    """站点数据统计面板测试：验证匿名跳转、普通用户 403、超管可看且数据正确。"""

    #zly: 每个用例前造一个超管、一个分类、一篇文章、一条评论。
    def setUp(self):
        self.url = reverse('servermanager:site_statistics')
        self.superuser = BlogUser.objects.create_superuser(
            email='zly_admin@example.com',
            username='zly_admin',
            password='zly_admin_123')
        self.category = Category.objects.create(name='统计测试分类')
        self.article = Article.objects.create(
            title='统计测试文章',
            body='统计测试正文',
            author=self.superuser,
            category=self.category,
            status='p',
            views=42)
        #zly: 评论设为待审核，避免 post_save 信号触发真实邮件线程。
        Comment.objects.create(
            body='统计测试评论',
            author=self.superuser,
            article=self.article,
            is_enable=False)

    #zly: 未登录访问统计面板应跳转登录页。
    def test_anonymous_user_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    #zly: 普通登录用户访问统计面板应返回 403。
    def test_normal_user_forbidden(self):
        user = BlogUser.objects.create_user(
            username='zly_normal',
            email='zly_normal@example.com',
            password='zly_normal_123')
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    #zly: 超级管理员可以查看面板，且核心指标与造的数据一致。
    def test_superuser_can_view_statistics(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        stats = response.context['stats']
        self.assertEqual(stats['article_total'], 1)
        self.assertEqual(stats['article_published'], 1)
        self.assertEqual(stats['article_draft'], 0)
        self.assertEqual(stats['article_views'], 42)
        self.assertEqual(stats['comment_total'], 1)
        self.assertEqual(stats['comment_pending'], 1)
        self.assertEqual(stats['user_total'], 1)
        self.assertEqual(stats['category_total'], 1)

    #zly: 后台首页应出现"站点数据统计"入口，避免入口模板失效。
    def test_admin_index_has_statistics_entry(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '站点数据统计')


#zly: 邮件失败重试测试：覆盖重试成功、失败、空收件人、批量重试与管理命令。
class EmailServiceTest(TestCase):
    """邮件失败重试测试：用 mock 模拟 SMTP 结果，验证重试次数与日志字段。"""

    #zly: 构造 mock 邮件对象，send 的返回值/异常由 side_effect 控制。
    def _mock_message(self, mock_cls, send_side_effect):
        message = mock_cls.return_value
        message.send.side_effect = send_side_effect
        return message

    #zly: 重试成功：更新发送结果、重试次数与最后重试时间，并清空失败原因。
    @mock.patch('servermanager.services.EmailMultiAlternatives')
    def test_retry_success(self, mock_cls):
        log = EmailSendLog.objects.create(
            emailto='a@example.com',
            title='标题',
            content='<p>正文</p>',
            send_result=False)
        self._mock_message(mock_cls, [1])
        self.assertTrue(EmailService.retry(log))
        log.refresh_from_db()
        self.assertTrue(log.send_result)
        self.assertEqual(log.retry_count, 1)
        self.assertIsNotNone(log.last_retry_time)
        self.assertEqual(log.error_message, '')
        self.assertEqual(mock_cls.return_value.send.call_count, 1)

    #zly: 重试仍失败：保留失败状态，记录失败原因与重试次数。
    @mock.patch('servermanager.services.EmailMultiAlternatives')
    def test_retry_failure(self, mock_cls):
        log = EmailSendLog.objects.create(
            emailto='a@example.com',
            title='标题',
            content='<p>正文</p>',
            send_result=False)
        self._mock_message(mock_cls, Exception('smtp down'))
        self.assertFalse(EmailService.retry(log))
        log.refresh_from_db()
        self.assertFalse(log.send_result)
        self.assertEqual(log.retry_count, 1)
        self.assertIn('smtp down', log.error_message)

    #zly: 收件人为空：不发送邮件，直接把失败原因写入日志。
    @mock.patch('servermanager.services.EmailMultiAlternatives')
    def test_retry_empty_recipient(self, mock_cls):
        log = EmailSendLog.objects.create(
            emailto='',
            title='标题',
            content='<p>正文</p>',
            send_result=False)
        self.assertFalse(EmailService.retry(log))
        log.refresh_from_db()
        self.assertEqual(log.error_message, '收件人为空')
        mock_cls.assert_not_called()

    #zly: 批量重试：只处理失败邮件，返回总数与成功数，已成功邮件不重试。
    @mock.patch('servermanager.services.EmailMultiAlternatives')
    def test_retry_failed_batch(self, mock_cls):
        EmailSendLog.objects.create(
            emailto='a@example.com', title='失败1', content='c', send_result=False)
        EmailSendLog.objects.create(
            emailto='b@example.com', title='失败2', content='c', send_result=False)
        EmailSendLog.objects.create(
            emailto='c@example.com', title='已成功', content='c', send_result=True)
        self._mock_message(mock_cls, [1, 1])
        total, success = EmailService.retry_failed()
        self.assertEqual(total, 2)
        self.assertEqual(success, 2)
        self.assertEqual(EmailSendLog.objects.filter(retry_count=1).count(), 2)
        self.assertEqual(EmailSendLog.objects.get(title='已成功').retry_count, 0)

    #zly: 管理命令：默认重试全部失败邮件，--limit 可限制单次重试数量。
    @mock.patch('servermanager.services.EmailMultiAlternatives')
    def test_retry_failed_emails_command(self, mock_cls):
        EmailSendLog.objects.create(
            emailto='a@example.com', title='失败1', content='c', send_result=False)
        EmailSendLog.objects.create(
            emailto='b@example.com', title='失败2', content='c', send_result=False)
        self._mock_message(mock_cls, [1, 1])
        call_command('retry_failed_emails')
        self.assertEqual(EmailSendLog.objects.filter(retry_count=1).count(), 2)

        EmailSendLog.objects.update(send_result=False, retry_count=0)
        self._mock_message(mock_cls, [1, 1])
        call_command('retry_failed_emails', '--limit', '1')
        self.assertEqual(EmailSendLog.objects.filter(retry_count=1).count(), 1)
