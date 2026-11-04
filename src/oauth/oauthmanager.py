#xcz: 封装各第三方平台的 OAuth 授权、令牌交换和用户资料读取流程。
import json
import logging
import os
import urllib.parse
from abc import ABCMeta, abstractmethod

import requests

from djangoblog.utils import cache_decorator
from oauth.models import OAuthConfig, OAuthUser

logger = logging.getLogger(__name__)


#xcz: 表示授权码无法换取访问令牌时的 OAuth 流程错误。
class OAuthAccessTokenError(Exception):
    """
    OAuth 授权失败异常：当第三方平台换取 access_token 失败（返回异常）时抛出。
    """


# 保留旧名称，避免已有集成代码因异常类重命名而失效。
OAuthAccessTokenException = OAuthAccessTokenError


#xcz: 定义各 OAuth 平台共用的授权接口和 HTTP 请求方法。
class BaseOauthManager(metaclass=ABCMeta):
    """
    第三方 OAuth 平台管理器的抽象基类。
    定义各平台（微博 / Google / GitHub / Facebook / QQ）通用的授权流程接口与通用请求方法，
    子类通过实现抽象方法并覆写各平台 URL 常量来对接具体平台。
    """
    # 第三方授权页地址（子类覆写）
    AUTH_URL = None
    # 用 code 换取 access_token 的接口地址（子类覆写）
    TOKEN_URL = None
    # 获取用户信息的接口地址（子类覆写）
    API_URL = None
    # 平台图标名 / 类型标识，须与 OAuthConfig.type 一致（子类覆写）
    ICON_NAME = None

    #xcz: 初始化表单控件或平台令牌状态。
    def __init__(self, access_token=None, openid=None):
        # 保存访问令牌与第三方用户唯一标识，后续换取用户信息时使用
        self.access_token = access_token
        self.openid = openid

    #xcz: 判断实例是否已获得访问令牌。
    @property
    def is_access_token_set(self):
        """是否已获取 access_token。"""
        return self.access_token is not None

    #xcz: 判断访问令牌和第三方用户标识是否都已具备。
    @property
    def is_authorized(self):
        """是否已完成授权（同时具备 access_token 与 openid）。"""
        return self.is_access_token_set and self.access_token is not None and self.openid is not None

    #xcz: 根据平台参数构造并编码第三方授权请求地址。
    @abstractmethod
    def get_authorization_url(self, nexturl='/'):
        """生成第三方授权页地址（子类实现）。"""
        pass

    #xcz: 使用回调授权码向第三方换取访问令牌。
    @abstractmethod
    def get_access_token_by_code(self, code):
        """用授权回调返回的 code 换取 access_token（子类实现）。"""
        pass

    #xcz: 请求第三方用户资料并转换为 OAuthUser 对象。
    @abstractmethod
    def get_oauth_userinfo(self):
        """调用第三方接口获取用户信息并组装 OAuthUser（子类实现）。"""
        pass

    #xcz: 从平台返回的资料中提取头像地址。
    @abstractmethod
    def get_picture(self, metadata):
        """从第三方返回的原始数据中提取头像地址（子类实现）。"""
        pass

    #xcz: 发送通用 GET 请求并记录响应内容。
    def do_get(self, url, params, headers=None):
        """通用 GET 请求：发送请求、记录响应日志并返回响应文本。"""
        rsp = requests.get(url=url, params=params, headers=headers)
        logger.info(rsp.text)
        return rsp.text

    #xcz: 发送通用 POST 请求并记录响应内容。
    def do_post(self, url, params, headers=None):
        """通用 POST 请求：发送请求、记录响应日志并返回响应文本。"""
        rsp = requests.post(url, params, headers=headers)
        logger.info(rsp.text)
        return rsp.text

    #xcz: 按平台标识读取 OAuthConfig；没有配置时返回空值。
    def get_config(self):
        """根据平台类型读取数据库中的 OAuthConfig 配置（不存在则返回 None）。"""
        value = OAuthConfig.objects.filter(type=self.ICON_NAME)
        return value[0] if value else None


#xcz: 实现微博平台的授权码交换和用户资料读取。
class WBOauthManager(BaseOauthManager):
    """
    微博 OAuth 管理器：对接微博开放平台，实现授权、换取 token、获取用户信息。
    """
    # 微博各接口地址与平台标识
    AUTH_URL = 'https://api.weibo.com/oauth2/authorize'
    TOKEN_URL = 'https://api.weibo.com/oauth2/access_token'
    API_URL = 'https://api.weibo.com/2/users/show.json'
    ICON_NAME = 'weibo'

    #xcz: 读取微博平台配置并初始化客户端凭据和令牌状态。
    def __init__(self, access_token=None, openid=None):
        # 从数据库读取微博平台配置，填充 client_id / client_secret / callback_url
        config = self.get_config()
        self.client_id = config.appkey if config else ''
        self.client_secret = config.appsecret if config else ''
        self.callback_url = config.callback_url if config else ''
        super().__init__(
            access_token=access_token,
            openid=openid)

    #xcz: 按微博平台协议构造并编码授权请求地址。
    def get_authorization_url(self, nexturl='/'):
        """拼装微博授权页地址，并将回调后需跳转的页面地址附在 redirect_uri 中。"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.callback_url + '&next_url=' + nexturl
        }
        url = self.AUTH_URL + "?" + urllib.parse.urlencode(params)
        return url

    #xcz: 使用授权码向微博换取访问令牌，并处理平台响应格式。
    def get_access_token_by_code(self, code):
        """用授权码向微博换取 access_token，成功后再调用接口获取用户信息。"""
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.callback_url
        }
        rsp = self.do_post(self.TOKEN_URL, params)

        obj = json.loads(rsp)
        # 换取成功则保存 access_token 与 uid，并立即拉取用户信息
        #xcz: 仅在第三方响应包含 access_token 时保存令牌并继续读取用户资料。
        if 'access_token' in obj:
            self.access_token = str(obj['access_token'])
            self.openid = str(obj['uid'])
            return self.get_oauth_userinfo()
        else:
            raise OAuthAccessTokenError(rsp)

    #xcz: 读取微博用户资料并映射为 OAuthUser 对象。
    def get_oauth_userinfo(self):
        """调用微博用户信息接口，将返回数据映射为 OAuthUser 对象。"""
        if not self.is_authorized:
            return None
        params = {
            'uid': self.openid,
            'access_token': self.access_token
        }
        rsp = self.do_get(self.API_URL, params)
        try:
            datas = json.loads(rsp)
            user = OAuthUser()
            user.metadata = rsp
            user.picture = datas['avatar_large']
            user.nickname = datas['screen_name']
            user.openid = datas['id']
            user.type = 'weibo'
            user.token = self.access_token
            if 'email' in datas and datas['email']:
                user.email = datas['email']
            return user
        except Exception as e:
            logger.error(e)
            logger.error('weibo oauth error.rsp:' + rsp)
            return None

    #xcz: 从微博返回的数据中提取头像地址。
    def get_picture(self, metadata):
        """从微博返回的原始数据中提取头像地址。"""
        datas = json.loads(metadata)
        return datas['avatar_large']


#xcz: 为需要代理访问的平台提供通用 HTTP 代理请求。
class ProxyManagerMixin:
    """
    代理请求 Mixin：当系统配置了 HTTP_PROXY 环境变量时，为 HTTP 请求自动附加代理。
    """
    #xcz: 初始化表单控件或平台令牌状态。
    def __init__(self, *args, **kwargs):
        # 读取环境变量，决定是否启用代理
        if os.environ.get("HTTP_PROXY"):
            self.proxies = {
                "http": os.environ.get("HTTP_PROXY"),
                "https": os.environ.get("HTTP_PROXY")
            }
        else:
            self.proxies = None

    #xcz: 通过已配置代理发送 GET 请求并记录响应。
    def do_get(self, url, params, headers=None):
        """带代理的通用 GET 请求。"""
        rsp = requests.get(url=url, params=params, headers=headers, proxies=self.proxies)
        logger.info(rsp.text)
        return rsp.text

    #xcz: 通过已配置代理发送 POST 请求并记录响应。
    def do_post(self, url, params, headers=None):
        """带代理的通用 POST 请求。"""
        rsp = requests.post(url, params, headers=headers, proxies=self.proxies)
        logger.info(rsp.text)
        return rsp.text


#xcz: 实现 Google 平台的授权码交换和用户资料读取。
class GoogleOauthManager(ProxyManagerMixin, BaseOauthManager):
    """
    Google OAuth 管理器：对接 Google 账号授权，走代理访问（海外平台）。
    """
    # Google 各接口地址与平台标识
    AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
    TOKEN_URL = 'https://www.googleapis.com/oauth2/v4/token'
    API_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'
    ICON_NAME = 'google'

    #xcz: 读取Google平台配置并初始化客户端凭据和令牌状态。
    def __init__(self, access_token=None, openid=None):
        # 从数据库读取 Google 平台配置，填充 client_id / client_secret / callback_url
        config = self.get_config()
        self.client_id = config.appkey if config else ''
        self.client_secret = config.appsecret if config else ''
        self.callback_url = config.callback_url if config else ''
        super().__init__(
            access_token=access_token,
            openid=openid)

    #xcz: 按Google平台协议构造并编码授权请求地址。
    def get_authorization_url(self, nexturl='/'):
        """拼装 Google 授权页地址，申请 openid 与 email 两个 scope。"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.callback_url,
            'scope': 'openid email',
        }
        url = self.AUTH_URL + "?" + urllib.parse.urlencode(params)
        return url

    #xcz: 使用授权码向Google换取访问令牌，并处理平台响应格式。
    def get_access_token_by_code(self, code):
        """用授权码向 Google 换取 access_token，成功后返回 token 本身。"""
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': code,

            'redirect_uri': self.callback_url
        }
        rsp = self.do_post(self.TOKEN_URL, params)

        obj = json.loads(rsp)

        if 'access_token' in obj:
            self.access_token = str(obj['access_token'])
            # Google 的 openid 使用返回的 id_token 标识
            self.openid = str(obj['id_token'])
            logger.info(self.ICON_NAME + ' oauth ' + rsp)
            return self.access_token
        else:
            raise OAuthAccessTokenError(rsp)

    #xcz: 读取Google用户资料并映射为 OAuthUser 对象。
    def get_oauth_userinfo(self):
        """调用 Google 用户信息接口，将返回数据映射为 OAuthUser 对象。"""
        if not self.is_authorized:
            return None
        params = {
            'access_token': self.access_token
        }
        rsp = self.do_get(self.API_URL, params)
        try:

            datas = json.loads(rsp)
            user = OAuthUser()
            user.metadata = rsp
            user.picture = datas['picture']
            user.nickname = datas['name']
            user.openid = datas['sub']
            user.token = self.access_token
            user.type = 'google'
            if datas['email']:
                user.email = datas['email']
            return user
        except Exception as e:
            logger.error(e)
            logger.error('google oauth error.rsp:' + rsp)
            return None

    #xcz: 从Google返回的数据中提取头像地址。
    def get_picture(self, metadata):
        """从 Google 返回的原始数据中提取头像地址。"""
        datas = json.loads(metadata)
        return datas['picture']


#xcz: 实现 GitHub 授权流程，并在必要时单独获取用户邮箱。
class GitHubOauthManager(ProxyManagerMixin, BaseOauthManager):
    """
    GitHub OAuth 管理器：对接 GitHub 授权，走代理访问（海外平台）。
    """
    # GitHub 各接口地址与平台标识（EMAILS_API_URL 用于邮箱不可见时单独拉取）
    AUTH_URL = 'https://github.com/login/oauth/authorize'
    TOKEN_URL = 'https://github.com/login/oauth/access_token'
    API_URL = 'https://api.github.com/user'
    EMAILS_API_URL = 'https://api.github.com/user/emails'
    ICON_NAME = 'github'

    #xcz: 读取GitHub平台配置并初始化客户端凭据和令牌状态。
    def __init__(self, access_token=None, openid=None):
        # 从数据库读取 GitHub 平台配置，填充 client_id / client_secret / callback_url
        config = self.get_config()
        self.client_id = config.appkey if config else ''
        self.client_secret = config.appsecret if config else ''
        self.callback_url = config.callback_url if config else ''
        super().__init__(
            access_token=access_token,
            openid=openid)

    #xcz: 按GitHub平台协议构造并编码授权请求地址。
    def get_authorization_url(self, next_url='/'):
        """拼装 GitHub 授权页地址，申请读取用户邮箱的 user:email scope。"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': f'{self.callback_url}&next_url={next_url}',
            'scope': 'user:email'
        }
        url = self.AUTH_URL + "?" + urllib.parse.urlencode(params)
        return url

    #xcz: 使用授权码向GitHub换取访问令牌，并处理平台响应格式。
    def get_access_token_by_code(self, code):
        """用授权码向 GitHub 换取 access_token（GitHub 返回表单格式，需手动解析）。"""
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'code': code,

            'redirect_uri': self.callback_url
        }
        rsp = self.do_post(self.TOKEN_URL, params)

        # GitHub 的 token 响应为 urlencoded 表单格式，用 parse_qs 解析
        from urllib import parse
        r = parse.parse_qs(rsp)
        if 'access_token' in r:
            self.access_token = (r['access_token'][0])
            return self.access_token
        else:
            raise OAuthAccessTokenError(rsp)

    #xcz: 读取GitHub用户资料并映射为 OAuthUser 对象。
    def get_oauth_userinfo(self):
        """调用 GitHub 用户信息接口，将返回数据映射为 OAuthUser 对象。"""
        # 通过 Bearer token 方式请求用户信息
        rsp = self.do_get(self.API_URL, params={}, headers={
            "Authorization": "Bearer " + self.access_token
        })
        try:
            datas = json.loads(rsp)
            user = OAuthUser()
            user.picture = datas['avatar_url']
            user.nickname = datas['name']
            user.openid = datas['id']
            user.type = 'github'
            user.token = self.access_token
            user.metadata = rsp
            if 'email' in datas and datas['email']:
                user.email = datas['email']
            else:
                # If email is not public, fetch from /user/emails endpoint
                # 邮箱不可见时，额外请求 /user/emails 接口获取邮箱
                try:
                    emails_rsp = self.do_get(self.EMAILS_API_URL, params={}, headers={
                        "Authorization": "Bearer " + self.access_token
                    })
                    emails = json.loads(emails_rsp)
                    # Find verified email, prioritizing primary verified email
                    # 优先取主验证邮箱，其次取任一已验证邮箱
                    for email_data in emails:
                        #xcz: 只考虑第三方标记为已验证的邮箱，避免绑定未经验证的地址。
                        if email_data.get('verified'):
                            if email_data.get('primary'):
                                # Primary verified email takes priority
                                user.email = email_data.get('email')
                                break
                            elif not user.email:
                                # Use first verified email as fallback
                                user.email = email_data.get('email')
                except Exception as e:
                    logger.warning(
                        'Failed to fetch private email from GitHub API. '
                        'User login will fail if email is required: %s',
                        e,
                    )
            return user
        except Exception as e:
            logger.error(e)
            logger.error('github oauth error.rsp:' + rsp)
            return None

    #xcz: 从GitHub返回的数据中提取头像地址。
    def get_picture(self, metadata):
        """从 GitHub 返回的原始数据中提取头像地址。"""
        datas = json.loads(metadata)
        return datas['avatar_url']


#xcz: 实现 Facebook 平台的授权码交换和用户资料读取。
class FaceBookOauthManager(ProxyManagerMixin, BaseOauthManager):
    """
    Facebook OAuth 管理器：对接 Facebook 授权，走代理访问（海外平台）。
    """
    # Facebook 各接口地址与平台标识
    AUTH_URL = 'https://www.facebook.com/v16.0/dialog/oauth'
    TOKEN_URL = 'https://graph.facebook.com/v16.0/oauth/access_token'
    API_URL = 'https://graph.facebook.com/me'
    ICON_NAME = 'facebook'

    #xcz: 读取Facebook平台配置并初始化客户端凭据和令牌状态。
    def __init__(self, access_token=None, openid=None):
        # 从数据库读取 Facebook 平台配置，填充 client_id / client_secret / callback_url
        config = self.get_config()
        self.client_id = config.appkey if config else ''
        self.client_secret = config.appsecret if config else ''
        self.callback_url = config.callback_url if config else ''
        super().__init__(
            access_token=access_token,
            openid=openid)

    #xcz: 按Facebook平台协议构造并编码授权请求地址。
    def get_authorization_url(self, next_url='/'):
        """拼装 Facebook 授权页地址，申请 email 与公开资料 scope。"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.callback_url,
            'scope': 'email,public_profile'
        }
        url = self.AUTH_URL + "?" + urllib.parse.urlencode(params)
        return url

    #xcz: 使用授权码向Facebook换取访问令牌，并处理平台响应格式。
    def get_access_token_by_code(self, code):
        """用授权码向 Facebook 换取 access_token，成功后返回 token 本身。"""
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            # 'grant_type': 'authorization_code',
            'code': code,

            'redirect_uri': self.callback_url
        }
        rsp = self.do_post(self.TOKEN_URL, params)

        obj = json.loads(rsp)
        if 'access_token' in obj:
            token = str(obj['access_token'])
            self.access_token = token
            return self.access_token
        else:
            raise OAuthAccessTokenError(rsp)

    #xcz: 读取Facebook用户资料并映射为 OAuthUser 对象。
    def get_oauth_userinfo(self):
        """调用 Facebook 用户信息接口，将返回数据映射为 OAuthUser 对象。"""
        # 显式指定需要返回的字段，避免默认字段缺失
        params = {
            'access_token': self.access_token,
            'fields': 'id,name,picture,email'
        }
        try:
            rsp = self.do_get(self.API_URL, params)
            datas = json.loads(rsp)
            user = OAuthUser()
            user.nickname = datas['name']
            user.openid = datas['id']
            user.type = 'facebook'
            user.token = self.access_token
            user.metadata = rsp
            if 'email' in datas and datas['email']:
                user.email = datas['email']
            # Facebook 头像嵌套在 picture.data.url 中，逐层取值
            if 'picture' in datas and datas['picture'] and datas['picture']['data'] and datas['picture']['data']['url']:
                user.picture = str(datas['picture']['data']['url'])
            return user
        except Exception as e:
            logger.error(e)
            return None

    #xcz: 从Facebook返回的数据中提取头像地址。
    def get_picture(self, metadata):
        """从 Facebook 返回的原始数据中提取头像地址。"""
        datas = json.loads(metadata)
        return str(datas['picture']['data']['url'])


#xcz: 实现 QQ 授权流程，并单独请求第三方用户 openid。
class QQOauthManager(BaseOauthManager):
    """
    QQ OAuth 管理器：对接 QQ 互联授权。QQ 的 openid 与 token 分两步获取，故单独实现 get_open_id。
    """
    # QQ 各接口地址与平台标识
    AUTH_URL = 'https://graph.qq.com/oauth2.0/authorize'
    TOKEN_URL = 'https://graph.qq.com/oauth2.0/token'
    API_URL = 'https://graph.qq.com/user/get_user_info'
    OPEN_ID_URL = 'https://graph.qq.com/oauth2.0/me'
    ICON_NAME = 'qq'

    #xcz: 读取QQ平台配置并初始化客户端凭据和令牌状态。
    def __init__(self, access_token=None, openid=None):
        # 从数据库读取 QQ 平台配置，填充 client_id / client_secret / callback_url
        config = self.get_config()
        self.client_id = config.appkey if config else ''
        self.client_secret = config.appsecret if config else ''
        self.callback_url = config.callback_url if config else ''
        super().__init__(
            access_token=access_token,
            openid=openid)

    #xcz: 按QQ平台协议构造并编码授权请求地址。
    def get_authorization_url(self, next_url='/'):
        """拼装 QQ 授权页地址，并将回调后需跳转的页面地址附在 redirect_uri 中。"""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.callback_url + '&next_url=' + next_url,
        }
        url = self.AUTH_URL + "?" + urllib.parse.urlencode(params)
        return url

    #xcz: 使用授权码向QQ换取访问令牌，并处理平台响应格式。
    def get_access_token_by_code(self, code):
        """用授权码向 QQ 换取 access_token（QQ 返回 urlencoded 格式）。"""
        params = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.callback_url
        }
        rsp = self.do_get(self.TOKEN_URL, params)
        if rsp:
            d = urllib.parse.parse_qs(rsp)
            if 'access_token' in d:
                token = d['access_token']
                self.access_token = token[0]
                return token
        else:
            raise OAuthAccessTokenError(rsp)

    #xcz: 调用 QQ 接口解析并保存独立返回的 openid。
    def get_open_id(self):
        """单独调用接口获取 QQ 用户的 openid（QQ 的 openid 需独立请求）。"""
        if self.is_access_token_set:
            params = {
                'access_token': self.access_token
            }
            rsp = self.do_get(self.OPEN_ID_URL, params)
            if rsp:
                # 返回体形如 callback(...); 需剥离外层包裹后按 JSON 解析
                #xcz: QQ 响应带有 callback 包装，先移除包装才能解析 JSON。
                rsp = rsp.replace(
                    'callback(', '').replace(
                    ')', '').replace(
                    ';', '')
                obj = json.loads(rsp)
                openid = str(obj['openid'])
                self.openid = openid
                return openid

    #xcz: 读取QQ用户资料并映射为 OAuthUser 对象。
    def get_oauth_userinfo(self):
        """调用 QQ 用户信息接口，将返回数据映射为 OAuthUser 对象。"""
        openid = self.get_open_id()
        if openid:
            params = {
                'access_token': self.access_token,
                'oauth_consumer_key': self.client_id,
                'openid': self.openid
            }
            rsp = self.do_get(self.API_URL, params)
            logger.info(rsp)
            obj = json.loads(rsp)
            user = OAuthUser()
            user.nickname = obj['nickname']
            user.openid = openid
            user.type = 'qq'
            user.token = self.access_token
            user.metadata = rsp
            if 'email' in obj:
                user.email = obj['email']
            if 'figureurl' in obj:
                user.picture = str(obj['figureurl'])
            return user

    #xcz: 从QQ返回的数据中提取头像地址。
    def get_picture(self, metadata):
        """从 QQ 返回的原始数据中提取头像地址。"""
        datas = json.loads(metadata)
        return str(datas['figureurl'])


#xcz: 读取已启用平台配置并构造相应管理器。
@cache_decorator(expiration=100 * 60)
def get_oauth_apps():
    """获取所有「已启用」的第三方平台管理器实例（结果缓存 100 分钟）。"""
    configs = OAuthConfig.objects.filter(is_enable=True).all()
    if not configs:
        return []
    # 已启用平台的类型集合
    configtypes = [x.type for x in configs]
    # 遍历 BaseOauthManager 的所有子类，实例化类型匹配的平台管理器
    applications = BaseOauthManager.__subclasses__()
    apps = [x() for x in applications if x().ICON_NAME.lower() in configtypes]
    return apps


#xcz: 按平台类型查找 OAuth 管理器实例。
def get_manager_by_type(type):
    """根据平台类型字符串（如 github）查找对应的平台管理器实例，找不到返回 None。"""
    applications = get_oauth_apps()
    if applications:
        finds = list(
            filter(
                lambda x: x.ICON_NAME.lower() == type.lower(),
                applications))
        if finds:
            return finds[0]
    return None
