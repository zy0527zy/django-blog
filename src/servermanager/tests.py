#zly: 模块说明：servermanager 的自动化测试，覆盖微信机器人消息处理、文章检索与管理员命令执行。
# servermanager/tests.py
# Django单元测试文件，用于对servermanager模块的各类功能编写自动化测试用例
from django.test import Client, RequestFactory, TestCase  #zly: 导入 Django 测试相关工具类
from werobot.messages.messages import TextMessage  #zly: 导入微信机器人文本消息实体

from accounts.models import BlogUser  #zly: 导入博客用户模型
from blog.models import Article, Category  #zly: 导入博客分类、文章模型
from servermanager.api.commonapi import ChatGPT  #zly: 导入 ChatGPT 接口类

from .models import commands  #zly: 导入当前 app 的命令数据表模型
from .robot import (  #zly: 导入消息处理器、命令处理器、文章搜索/分类/最新文章处理函数
    CommandHandler,
    MessageHandler,
    category,
    recents,
    search,
)


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
