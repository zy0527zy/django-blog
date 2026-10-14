import logging
# Create your views here.
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from django.utils.http import url_has_allowed_host_and_scheme

from djangoblog.blog_signals import oauth_user_login_signal
from djangoblog.utils import get_current_site
from djangoblog.utils import send_email, get_sha256
from oauth.forms import RequireEmailForm
from .models import OAuthUser
from .oauthmanager import get_manager_by_type, OAuthAccessTokenException

logger = logging.getLogger(__name__)


def get_redirecturl(request):
    """
    获取安全的登录后重定向 URL。
    1. 优先从 GET 参数 next_url 中获取。
    2. 过滤非法 URL（如外部恶意地址），仅允许跳转到当前站点或相对路径。
    3. 默认重定向到首页 /。
    """
    nexturl = request.GET.get('next_url', None)
    # 如果没有 next_url，或者指向登录页本身，直接返回首页
    if not nexturl or nexturl == '/login/' or nexturl == '/login':
        return '/'

    # Only allow relative URLs or URLs pointing to the current host
    # 安全校验：确保重定向地址属于当前域名，防止开放重定向漏洞
    site_domain = get_current_site().domain
    if url_has_allowed_host_and_scheme(
        url=nexturl,
        allowed_hosts={site_domain},
        require_https=request.is_secure()
    ):
        return nexturl

    # 非法 url 记录日志并返回首页
    logger.info('非法url:' + str(nexturl))
    return '/'


def oauthlogin(request):
    """
    发起 OAuth 登录请求。
    根据传入的 type（如 github、weibo），跳转到第三方平台的授权页面。
    """
    type = request.GET.get('type', None)
    # 如果没有指定 type，或者没有对应的 manager，直接返回首页
    if not type:
        return HttpResponseRedirect('/')
    manager = get_manager_by_type(type)
    if not manager:
        return HttpResponseRedirect('/')
    # 获取授权后需要跳转的页面
    nexturl = get_redirecturl(request)
    # 获取第三方平台的授权 URL 并重定向
    authorizeurl = manager.get_authorization_url(nexturl)
    return HttpResponseRedirect(authorizeurl)


def authorize(request):
    """
    OAuth 回调处理视图（核心逻辑）。
    1. 接收第三方平台返回的 code，换取 access_token。
    2. 获取第三方用户信息。
    3. 检查本地是否已有对应的 OAuthUser，若无则创建，有则更新。
    4. 绑定或创建本地 BlogUser，并执行登录。
    """
    type = request.GET.get('type', None)
    if not type:
        return HttpResponseRedirect('/')
    manager = get_manager_by_type(type)
    if not manager:
        return HttpResponseRedirect('/')
    code = request.GET.get('code', None)
    try:
        # 使用 code 换取 access_token
        rsp = manager.get_access_token_by_code(code)
    except OAuthAccessTokenException as e:
        # 换取 token 失败，记录警告并重定向首页
        logger.warning("OAuthAccessTokenException:" + str(e))
        return HttpResponseRedirect('/')
    except Exception as e:
        logger.error(e)
        rsp = None
    nexturl = get_redirecturl(request)
    if not rsp:
        # 如果换取失败，重新尝试跳转授权页
        return HttpResponseRedirect(manager.get_authorization_url(nexturl))
    
    # 获取第三方用户信息
    user = manager.get_oauth_userinfo()
    if user:
        # 防止第三方昵称为空
        if not user.nickname or not user.nickname.strip():
            user.nickname = "djangoblog" + timezone.now().strftime('%y%m%d%I%M%S')
        
        # 检查本地数据库中是否已存在该第三方用户
        try:
            temp = OAuthUser.objects.get(type=type, openid=user.openid)
            # 更新第三方用户信息
            temp.picture = user.picture
            temp.metadata = user.metadata
            temp.nickname = user.nickname
            user = temp
        except ObjectDoesNotExist:
            # 不存在则保持为新建状态
            pass
            
        # facebook的token过长，进行特殊处理
        if type == 'facebook':
            user.token = ''
            
        # 如果第三方返回了邮箱，则直接进行账号绑定/登录
        if user.email:
            with transaction.atomic(): # 数据库事务，保证用户创建和登录的一致性
                author = None
                try:
                    # 尝试获取已绑定的本地用户
                    author = get_user_model().objects.get(id=user.author_id)
                except ObjectDoesNotExist:
                    pass
                if not author:
                    # 根据邮箱在本地创建或获取用户
                    result = get_user_model().objects.get_or_create(email=user.email)
                    author = result[0]
                    if result[1]: # 如果是新创建的用户
                        try:
                            # 检查昵称是否已被占用
                            get_user_model().objects.get(username=user.nickname)
                        except ObjectDoesNotExist:
                            author.username = user.nickname
                        else:
                            # 昵称冲突则随机生成
                            author.username = "djangoblog" + timezone.now().strftime('%y%m%d%I%M%S')
                        author.source = 'authorize'
                        author.save()

                # 绑定本地用户并保存 OAuthUser
                user.author = author
                user.save()

                # 发送登录信号
                oauth_user_login_signal.send(
                    sender=authorize.__class__, id=user.id)
                # 执行 Django 登录
                login(request, author)
                # 设置session过期时间为2周（默认）
                request.session.set_expiry(settings.SESSION_COOKIE_AGE)
                # 设置登录标记 cookie
                response = HttpResponseRedirect(nexturl)
                response.set_cookie(
                    'logged_user',
                    'true',
                    max_age=settings.SESSION_COOKIE_AGE,
                    httponly=False,  # 允许 JavaScript 访问
                    samesite='Lax'
                )
                return response
        else:
            # 如果没有获取到邮箱，保存 OAuthUser 并引导用户去绑定邮箱页面
            user.save()
            url = reverse('oauth:require_email', kwargs={
                'oauthid': user.id
            })

            return HttpResponseRedirect(url)
    else:
        return HttpResponseRedirect(nexturl)


def emailconfirm(request, id, sign):
    """
    邮箱确认视图。
    处理用户点击邮件中的链接后的逻辑：验证签名，绑定本地用户，执行登录，发送欢迎邮件。
    """
    if not sign:
        return HttpResponseForbidden()
    # 验证签名：SECRET_KEY + id + SECRET_KEY 的哈希值必须一致，防止伪造链接
    if not get_sha256(settings.SECRET_KEY +
                      str(id) +
                      settings.SECRET_KEY).upper() == sign.upper():
        return HttpResponseForbidden()
    
    oauthuser = get_object_or_404(OAuthUser, pk=id)
    with transaction.atomic(): # 数据库事务
        if oauthuser.author:
            # 如果已经绑定过本地用户，直接获取
            author = get_user_model().objects.get(pk=oauthuser.author_id)
        else:
            # 根据邮箱创建或获取本地用户
            result = get_user_model().objects.get_or_create(email=oauthuser.email)
            author = result[0]
            if result[1]:
                author.source = 'emailconfirm'
                author.username = oauthuser.nickname.strip() if oauthuser.nickname.strip(
                ) else "djangoblog" + timezone.now().strftime('%y%m%d%I%M%S')
                author.save()
        
        # 完成 OAuthUser 与本地用户的绑定
        oauthuser.author = author
        oauthuser.save()
        
    # 发送登录信号并登录
    oauth_user_login_signal.send(
        sender=emailconfirm.__class__,
        id=oauthuser.id)
    login(request, author)
    # 设置session过期时间为2周（默认）
    request.session.set_expiry(settings.SESSION_COOKIE_AGE)

    # 拼接站点域名，用于发送邮件
    site = 'http://' + get_current_site().domain
    content = _('''
     <p>Congratulations, you have successfully bound your email address. You can use
      %(oauthuser_type)s to directly log in to this website without a password.</p>
       You are welcome to continue to follow this site, the address is
        <a href="%(site)s" rel="bookmark">%(site)s</a>
            Thank you again!
            <br />
        If the link above cannot be opened, please copy this link to your browser.
        %(site)s
    ''') % {'oauthuser_type': oauthuser.type, 'site': site}

    # 发送绑定成功邮件
    send_email(emailto=[oauthuser.email, ], title=_('Congratulations on your successful binding!'), content=content)
    url = reverse('oauth:bindsuccess', kwargs={
        'oauthid': id
    })
    url = url + '?type=success'
    # 设置登录标记 cookie
    response = HttpResponseRedirect(url)
    response.set_cookie(
        'logged_user',
        'true',
        max_age=settings.SESSION_COOKIE_AGE,
        httponly=False,  # 允许 JavaScript 访问
        samesite='Lax'
    )
    return response


class RequireEmailView(FormView):
    """
    绑定邮箱的表单视图。
    当第三方登录未获取到邮箱时，引导用户在此输入邮箱并发送验证邮件。
    """
    form_class = RequireEmailForm
    template_name = 'oauth/require_email.html'

    def get(self, request, *args, **kwargs):
        # 获取 OAuthUser，若不存在则返回 404
        oauthid = self.kwargs['oauthid']
        oauthuser = get_object_or_404(OAuthUser, pk=oauthid)
        if oauthuser.email:
            pass
            # 如果已经有邮箱，理论上可以直接登录，但此处保留逻辑待优化
            # return HttpResponseRedirect('/')

        return super(RequireEmailView, self).get(request, *args, **kwargs)

    def get_initial(self):
        # 初始化表单，将 oauthid 传入表单
        oauthid = self.kwargs['oauthid']
        return {
            'email': '',
            'oauthid': oauthid
        }

    def get_context_data(self, **kwargs):
        # 获取上下文数据，并传递第三方头像到模板
        oauthid = self.kwargs['oauthid']
        oauthuser = get_object_or_404(OAuthUser, pk=oauthid)
        if oauthuser.picture:
            kwargs['picture'] = oauthuser.picture
        return super(RequireEmailView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        # 表单验证通过后的逻辑：保存邮箱并发送验证邮件
        email = form.cleaned_data['email']
        oauthid = form.cleaned_data['oauthid']
        oauthuser = get_object_or_404(OAuthUser, pk=oauthid)
        oauthuser.email = email
        oauthuser.save()
        
        # 生成签名，用于邮件链接的安全校验
        sign = get_sha256(settings.SECRET_KEY +
                          str(oauthuser.id) + settings.SECRET_KEY)
        site = get_current_site().domain
        if settings.DEBUG:
            site = '127.0.0.1:8000'
        
        # 生成邮件确认链接
        path = reverse('oauth:email_confirm', kwargs={
            'id': oauthid,
            'sign': sign
        })
        url = "http://{site}{path}".format(site=site, path=path)

        # 构造邮件内容
        content = _("""
               <p>Please click the link below to bind your email</p>

                 <a href="%(url)s" rel="bookmark">%(url)s</a>

                 Thank you again!
                 <br />
                 If the link above cannot be opened, please copy this link to your browser.
                  <br />
                 %(url)s
                """) % {'url': url}
        # 发送验证邮件
        send_email(emailto=[email, ], title=_('Bind your email'), content=content)
        
        # 跳转到绑定成功提示页
        url = reverse('oauth:bindsuccess', kwargs={
            'oauthid': oauthid
        })
        url = url + '?type=email'
        return HttpResponseRedirect(url)


def bindsuccess(request, oauthid):
    """
    绑定成功/等待验证提示页。
    根据 type 参数显示不同的提示文案。
    """
    type = request.GET.get('type', None)
    oauthuser = get_object_or_404(OAuthUser, pk=oauthid)
    if type == 'email':
        title = _('Bind your email')
        content = _(
            'Congratulations, the binding is just one step away. '
            'Please log in to your email to check the email to complete the binding. Thank you.')
    else:
        title = _('Binding successful')
        content = _(
            "Congratulations, you have successfully bound your email address. You can use %(oauthuser_type)s"
            " to directly log in to this website without a password. You are welcome to continue to follow this site." % {
                'oauthuser_type': oauthuser.type})
    
    # 渲染绑定成功页面
    return render(request, 'oauth/bindsuccess.html', {
        'title': title,
        'content': content
    })