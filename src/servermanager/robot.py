"""
servermanager robot.py 微信机器人核心业务文件
功能：基于WeRoBot框架实现微信消息交互，提供文章检索、分类查询、管理员命令执行、AI对话等能力
会话存储优先使用Memcache缓存，缓存不可用时降级为本地文件存储
"""
import logging
import os
import re
import jsonpickle
from django.conf import settings
from werobot import WeRoBot
from werobot.replies import ArticlesReply, Article
from werobot.session.filestorage import FileStorage
from djangoblog.utils import get_sha256
from servermanager.api.blogapi import BlogApi
from servermanager.api.commonapi import ChatGPT, CommandHandler
from .MemcacheStorage import MemcacheStorage

# 初始化微信机器人实例，读取环境变量token，开启会话支持
robot = WeRoBot(token=os.environ.get('DJANGO_WEROBOT_TOKEN')
                    or 'lylinux', enable_session=True)
# 实例化memcache会话存储对象
memstorage = MemcacheStorage()

# 判断memcache是否可用，优先使用memcache存储会话；不可用切换文件存储
if memstorage.is_available:
    robot.config['SESSION_STORAGE'] = memstorage
else:
    # 若旧会话文件存在，先删除，使用全新文件存储会话
    if os.path.exists(os.path.join(settings.BASE_DIR, 'werobot_session')):
        os.remove(os.path.join(settings.BASE_DIR, 'werobot_session'))
    robot.config['SESSION_STORAGE'] = FileStorage(filename='werobot_session')

# 博客业务API实例
blogapi = BlogApi()
# 系统命令处理实例
cmd_handler = CommandHandler()
# 日志记录器
logger = logging.getLogger(__name__)


"""
将文章列表封装成微信图文消息回复
参数：articles文章对象列表，message微信原始消息对象
返回：组装好的图文消息对象
"""
def convert_to_article_reply(articles, message):
    reply = ArticlesReply(message=message)
    from blog.templatetags.blog_tags import truncatechars_content
    # 遍历文章，提取首图、标题、摘要、文章链接，构造图文卡片
    for post in articles:
        # 使用正则提取文章正文中第一张图片链接
        imgs = re.findall(r'(?:http\:|https\:)?\/\/.*\.(?:png|jpg)', post.body)
        imgurl = ''
        if imgs:
            imgurl = imgs[0]
        article = Article(
            title=post.title,
            description=truncatechars_content(post.body),
            img=imgurl,
            url=post.get_full_url()
        )
        reply.add_article(article)
    return reply


"""
微信消息过滤器：匹配 ?开头消息，执行博客文章搜索
例如：?django ，搜索包含django关键词的文章
"""
@robot.filter(re.compile(r"^\?.*"))
def search(message, session):
    s = message.content
    searchstr = str(s).replace('?', '')
    result = blogapi.search_articles(searchstr)
    if result:
        articles = list(map(lambda x: x.object, result))
        reply = convert_to_article_reply(articles, message)
        return reply
    else:
        return '没有找到相关文章。'


"""
微信消息过滤器：匹配 category 指令，获取博客全部文章分类名称
不区分大小写
"""
@robot.filter(re.compile(r'^category\s*$', re.I))
def category(message, session):
    categorys = blogapi.get_category_lists()
    content = ','.join(map(lambda x: x.name, categorys))
    return '所有文章分类目录：' + content


"""
微信消息过滤器：匹配 recent 指令，获取最新博客文章列表，返回图文消息
不区分大小写
"""
@robot.filter(re.compile(r'^recent\s*$', re.I))
def recents(message, session):
    articles = blogapi.get_recent_articles()
    if articles:
        reply = convert_to_article_reply(articles, message)
        return reply
    else:
        return "暂时还没有文章"


"""
微信消息过滤器：匹配 help 指令，返回机器人全部可用命令帮助文档
不区分大小写
"""
@robot.filter(re.compile('^help$', re.I))
def help(message, session):
    return '''欢迎关注!
            默认会与图灵机器人聊天~~
            你可以通过下面这些命令来获得信息
            ?关键字搜索文章.
            如?python.
            category获得文章分类目录及文章数.
            category-***获得该分类目录文章
            如category-python
            recent获得最新文章
            help获得帮助.
            weather:获得天气
            如weather:西安
            idcard:获得身份证信息
            如idcard:61048119xxxxxxxxxx
            music:音乐搜索
            如music:阴天快乐
            PS:以上标点符号都不支持中文标点~~
            '''


"""
微信消息过滤器：匹配 weather: 指令，天气查询功能（待开发）
不区分大小写
"""
@robot.filter(re.compile(r'^weather\:.*$', re.I))
def weather(message, session):
    return "建设中..."


"""
微信消息过滤器：匹配 idcard: 指令，身份证信息查询功能（待开发）
不区分大小写
"""
@robot.filter(re.compile(r'^idcard\:.*$', re.I))
def idcard(message, session):
    return "建设中..."


"""
默认消息处理器，所有不匹配上面过滤器的消息都会进入这里，交由MessageHandler处理
"""
@robot.handler
def echo(message, session):
    handler = MessageHandler(message, session)
    return handler.handler()


"""
微信消息业务处理类，负责管理员身份校验、密码验证、系统命令执行、用户会话信息维护
"""
class MessageHandler:
    """
    构造方法：初始化消息、会话、用户openid，从会话读取用户信息，无信息则新建用户信息对象
    """
    def __init__(self, message, session):
        userid = message.source
        self.message = message
        self.session = session
        self.userid = userid
        try:
            info = session[userid]
            self.userinfo = jsonpickle.decode(info)
        except Exception as e:
            # 会话读取异常，新建微信用户信息实例
            userinfo = WxUserInfo()
            self.userinfo = userinfo

    """属性：判断当前用户是否为管理员"""
    @property
    def is_admin(self):
        return self.userinfo.isAdmin

    """属性：判断管理员是否完成密码校验"""
    @property
    def is_password_set(self):
        return self.userinfo.isPasswordSet

    """将当前用户信息序列化，保存到会话存储中"""
    def save_session(self):
        info = jsonpickle.encode(self.userinfo)
        self.session[self.userid] = info

    """消息主处理逻辑，依次处理退出、管理员登录、密码校验、命令确认、AI对话逻辑"""
    def handler(self):
        info = self.message.content
        # 管理员输入EXIT，清空管理员状态，退出管理员模式
        if self.userinfo.isAdmin and info.upper() == 'EXIT':
            self.userinfo = WxUserInfo()
            self.save_session()
            return "退出成功"
        # 用户输入ADMIN，开启管理员身份验证流程
        if info.upper() == 'ADMIN':
            self.userinfo.isAdmin = True
            self.save_session()
            return "输入管理员密码"
        # 管理员模式下，还未完成密码验证，校验密码
        if self.userinfo.isAdmin and not self.userinfo.isPasswordSet:
            passwd = settings.WXADMIN
            # 测试环境密码固定为123
            if settings.TESTING:
                passwd = '123'
            # 双重sha256哈希比对密码
            if passwd.upper() == get_sha256(get_sha256(info)).upper():
                self.userinfo.isPasswordSet = True
                self.save_session()
                return "验证通过,请输入命令或者要执行的命令代码:输入helpme获得帮助"
            else:
                # 密码错误，累计错误次数，最多3次，超限重置管理员状态
                if self.userinfo.Count >= 3:
                    self.userinfo = WxUserInfo()
                    self.save_session()
                    return "超过验证次数"
                self.userinfo.Count += 1
                self.save_session()
                return "验证失败，请重新输入管理员密码:"
        # 管理员已完成密码校验，进入命令交互流程
        if self.userinfo.isAdmin and self.userinfo.isPasswordSet:
            # 待确认命令存在，用户回复Y，执行系统命令
            if self.userinfo.Command != '' and info.upper() == 'Y':
                return cmd_handler.run(self.userinfo.Command)
            else:
                # 输入helpme，返回命令帮助信息
                if info.upper() == 'HELPME':
                    return cmd_handler.get_help()
                # 保存用户输入的待执行命令，等待用户确认(Y)
                self.userinfo.Command = info
                self.save_session()
                return "确认执行: " + info + " 命令?"
        # 非管理员消息，交给ChatGPT进行对话回复
        return ChatGPT.chat(info)


"""微信用户会话信息实体类，存储管理员标记、密码校验状态、密码错误计数、待执行命令"""
class WxUserInfo():
    def __init__(self):
        self.isAdmin = False
        self.isPasswordSet = False
        self.Count = 0
        self.Command = ''
