# servermanager/tests.py
# Django单元测试文件，用于对servermanager模块的各类功能编写自动化测试用例
from django.test import Client, RequestFactory, TestCase # 导入Django测试相关工具类
from django.utils import timezone # 导入Django时间工具
from werobot.messages.messages import TextMessage # 导入微信机器人文本消息实体
from accounts.models import BlogUser # 导入博客用户模型
from blog.models import Category, Article # 导入博客分类、文章模型
from servermanager.api.commonapi import ChatGPT # 导入ChatGPT接口类
from .models import commands # 导入当前app的命令数据表模型
from .robot import MessageHandler, CommandHandler # 导入消息处理器、命令处理器
from .robot import search, category, recents # 导入文章搜索、分类、最新文章处理函数
# Create your tests here.
# servermanager模块测试类，继承Django测试基类TestCase
class ServerManagerTest(TestCase):
    # 测试前置方法，每个测试方法执行前自动运行，初始化测试客户端、请求工厂
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
    # 测试ChatGPT对话接口能否正常返回结果
    def test_chat_gpt(self):
        content = ChatGPT.chat("你好")
        self.assertIsNotNone(content) # 断言返回内容不为空
    # 综合测试方法，测试微信机器人各类消息、命令、文章相关功能
    def test_validate_comment(self):
        # 创建超级管理员测试账号
        user = BlogUser.objects.create_superuser(
            email="liangliangyy1@gmail.com",
            username="liangliangyy1",
            password="liangliangyy1")
        self.client.login(username='liangliangyy1', password='liangliangyy1') # 模拟登录管理员账号
        c = Category() # 创建文章分类实例
        c.name = "categoryccc"
        c.save() # 保存分类到测试数据库
        article = Article() # 创建文章实例
        article.title = "nicetitleccc"
        article.body = "nicecontentccc"
        article.author = user
        article.category = c
        article.type = 'a'
        article.status = 'p'
        article.save() # 保存文章到测试数据库
        s = TextMessage([]) # 构造微信文本消息对象
        s.content = "nice"
        rsp = search(s, None) # 调用文章搜索函数
        rsp = category(None, None) # 调用分类查询函数
        self.assertIsNotNone(rsp) # 断言返回结果不为空
        rsp = recents(None, None) # 调用获取最新文章函数
        self.assertTrue(rsp != '暂时还没有文章') # 断言存在文章数据
        cmd = commands() # 创建命令记录实例
        cmd.title = "test"
        cmd.command = "ls"
        cmd.describe = "test"
        cmd.save() # 保存测试命令
        cmdhandler = CommandHandler() # 实例化命令处理器
        rsp = cmdhandler.run('test') # 执行命令
        self.assertIsNotNone(rsp) # 断言命令执行有返回
        s.source = 'u' # 设置消息发送者标识
        s.content = 'test'
        msghandler = MessageHandler(s, {}) # 实例化微信消息处理器
        # msghandler.userinfo.isPasswordSet = True
        # msghandler.userinfo.isAdmin = True
        msghandler.handler() # 执行消息处理逻辑
        s.content = 'y'
        msghandler.handler() # 处理y指令消息
        s.content = 'idcard:12321233'
        msghandler.handler() # 处理身份证查询指令
        s.content = 'weather:上海'
        msghandler.handler() # 处理天气查询指令
        s.content = 'admin'
        msghandler.handler() # 处理管理员指令
        s.content = '123'
        msghandler.handler() # 处理普通消息
        s.content = 'exit'
        msghandler.handler() # 处理退出指令
