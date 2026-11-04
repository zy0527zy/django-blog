#swb: 处理账户注册、身份认证、邮箱验证和密码找回流程。
import logging

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import REDIRECT_FIELD_NAME, get_user_model, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import make_password
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from djangoblog.base_views import LoginFormView, LogoutRedirectView, SecureFormView
from djangoblog.utils import delete_sidebar_cache, generate_code, get_current_site, get_sha256, send_email

from . import utils
from .forms import ForgetPasswordCodeForm, ForgetPasswordForm, LoginForm, RegisterForm
from .models import BlogUser

logger = logging.getLogger(__name__)


# Create your views here.

#swb: 创建未激活账户，并发送带签名的邮箱验证链接。
class RegisterView(SecureFormView):
    """
    用户注册视图（重构版）

    使用 SecureFormView 基类，自动提供 CSRF 保护
    """
    form_class = RegisterForm
    template_name = 'account/registration_form.html'

    #swb: 处理已经通过输入校验的表单。
    def form_valid(self, form):
        # 基类通常已完成校验；这里再次确认，避免无效数据进入保存流程。
        if form.is_valid():
            # 先构造用户对象，再设为未激活状态，等待邮箱验证后才能登录。
            user = form.save(False)
            #swb: 新账户先保持未激活，直到用户完成邮箱链接验证。
            user.is_active = False
            # 记录用户通过站内注册创建，便于统计注册来源。
            user.source = 'Register'
            user.save(True)

            # 验证签名由站点密钥和用户 ID 派生，链接中不直接暴露站点密钥。
            site = get_current_site().domain
            #swb: 对账户标识进行签名，防止通过修改链接内容伪造激活请求。
            sign = get_sha256(get_sha256(settings.SECRET_KEY + str(user.id)))

            # 本地开发时使用本机地址，便于打开邮件中的验证链接。
            if settings.DEBUG:
                site = '127.0.0.1:8000'
            path = reverse('account:result')
            url = f"http://{site}{path}?type=validation&id={user.id}&sign={sign}"

            # 邮件正文包含验证链接，并提示用户也可以复制链接到浏览器。
            content = f"""
                            <p>请点击下面链接验证您的邮箱</p>

                            <a href="{url}" rel="bookmark">{url}</a>

                            再次感谢您！
                            <br />
                            如果上面链接无法打开，请将此链接复制至浏览器。
                            {url}
                            """
            # 将验证邮件发送到用户注册时填写的邮箱。
            send_email(
                emailto=[
                    user.email,
                ],
                title='验证您的电子邮箱',
                content=content)

            # 注册后跳转到结果页，提示用户检查邮箱。
            url = f"{reverse('accounts:result')}?type=register&id={user.id}"
            return HttpResponseRedirect(url)
        else:
            return self.render_to_response({
                'form': form
            })


#swb: 结束登录会话，并清理侧边栏缓存和登录 Cookie。
class LogoutView(LogoutRedirectView):
    """
    用户登出视图（重构版）

    使用 LogoutRedirectView 基类，自动禁用缓存
    """
    url = '/login/'

    #swb: 退出当前用户，并清理缓存及 Cookie 中的登录状态。
    def get(self, request, *args, **kwargs):
        # 清除 Django 登录状态，同时清理可能缓存用户信息的侧边栏。
        logout(request)
        delete_sidebar_cache()
        # 获取响应对象并删除登录标记 cookie
        response = super().get(request, *args, **kwargs)
        response.delete_cookie('logged_user')
        return response


#swb: 校验登录凭据、创建会话并设置登录状态 Cookie。
class LoginView(LoginFormView):
    """
    用户登录视图（重构版）

    使用 LoginFormView 基类，自动提供：
    - 敏感参数保护（password）
    - CSRF 保护
    - 禁用缓存
    """
    form_class = LoginForm
    template_name = 'account/login.html'
    success_url = '/'
    redirect_field_name = REDIRECT_FIELD_NAME

    #swb: 将登录后的跳转地址传给模板；未指定时默认跳转到首页。
    def get_context_data(self, **kwargs):
        # 将登录后的目标地址交给模板，以便表单提交时带回该参数。
        redirect_to = self.request.GET.get(self.redirect_field_name)
        if redirect_to is None:
            # 未指定返回地址时，默认进入网站首页。
            redirect_to = '/'
        kwargs['redirect_to'] = redirect_to

        return super().get_context_data(**kwargs)

    #swb: 处理已经通过输入校验的表单。
    def form_valid(self, form):
        # 使用 Django 认证表单校验凭据，并从校验后的表单取得用户对象。
        form = AuthenticationForm(data=self.request.POST, request=self.request)

        if form.is_valid():
            # 登录会影响侧边栏中的用户状态，因此使相关缓存失效。
            delete_sidebar_cache()
            logger.info(self.redirect_field_name)

            # 建立 Django 会话登录状态。
            auth.login(self.request, form.get_user())
            # 设置登录有效期
            if self.request.POST.get("remember"):
                # 勾选“记住我”时，使用项目配置的较长会话有效期。
                self.request.session.set_expiry(settings.REMEMBER_ME_LOGIN_TTL)
                cookie_max_age = settings.REMEMBER_ME_LOGIN_TTL
            else:
                # 使用Django默认的2周
                self.request.session.set_expiry(settings.SESSION_COOKIE_AGE)
                cookie_max_age = settings.SESSION_COOKIE_AGE

            # 获取响应对象并设置登录标记 cookie
            # 父类生成成功响应，并按 get_success_url() 处理跳转。
            response = super().form_valid(form)
            # 前端用此标记判断登录状态；HttpOnly=False 允许前端脚本读取。
            response.set_cookie(
                'logged_user',
                'true',
                max_age=cookie_max_age,
                httponly=False,  # 允许 JavaScript 访问
                samesite='Lax'
            )
            return response
            # return HttpResponseRedirect('/')
        else:
            return self.render_to_response({
                'form': form
            })

    #swb: 只允许站内跳转，避免登录后被重定向到外部网站。
    def get_success_url(self):
        # 仅允许跳转到当前请求主机上的地址，避免 next 参数导致外站跳转。
        redirect_to = self.request.POST.get(self.redirect_field_name)
        #swb: 将跳转目标限制在当前主机，避免重定向到外部网站。
        if not url_has_allowed_host_and_scheme(
                url=redirect_to, allowed_hosts=[
                    self.request.get_host()]):
            redirect_to = self.success_url
        return redirect_to


#swb: 显示注册结果，或验证邮箱激活链接。
def account_result(request):
    """处理注册结果提示与邮箱验证链接，并显示相应结果页面。"""
    # 查询参数用于区分注册提示和邮箱验证请求。
    type = request.GET.get('type')
    id = request.GET.get('id')

    # 用户编号无效时直接返回 404。
    user = get_object_or_404(get_user_model(), id=id)
    logger.info(type)
    # 已激活的账户无需重复验证，直接返回首页。
    if user.is_active:
        return HttpResponseRedirect('/')
    if type and type in ['register', 'validation']:
        if type == 'register':
            # 注册完成提示：验证邮件已发送，用户还需完成邮箱验证。
            content = '''
    恭喜您注册成功，一封验证邮件已经发送到您的邮箱，请验证您的邮箱后登录本站。
    '''
            title = '注册成功'
        else:
            # 重算用户签名并与链接参数比较，确认验证链接有效。
            c_sign = get_sha256(get_sha256(settings.SECRET_KEY + str(user.id)))
            sign = request.GET.get('sign')
            #swb: 重新计算并比对签名，通过后才激活账户。
            if sign != c_sign:
                return HttpResponseForbidden()
            # 签名有效后激活账户，并保存状态变更。
            #swb: 只有签名匹配后才启用账户。
            user.is_active = True
            user.save()
            content = '''
            恭喜您已经成功的完成邮箱验证，您现在可以使用您的账号来登录本站。
            '''
            title = '验证成功'
        # 使用统一的结果模板展示标题和提示正文。
        return render(request, 'account/result.html', {
            'title': title,
            'content': content
        })
    else:
        return HttpResponseRedirect('/')


#swb: 保存通过校验的新密码，并引导用户返回登录页。
class ForgetPasswordView(SecureFormView):
    """
    忘记密码视图（重构版）

    使用 SecureFormView 基类，自动提供 CSRF 保护
    """
    form_class = ForgetPasswordForm
    template_name = 'account/forget_password.html'

    #swb: 处理已经通过输入校验的表单。
    def form_valid(self, form):
        # 按邮箱定位用户，将新密码哈希后保存，避免明文存储密码。
        if form.is_valid():
            blog_user = BlogUser.objects.filter(email=form.cleaned_data.get("email")).get()
            #swb: 将新密码哈希后再保存到数据库。
            blog_user.password = make_password(form.cleaned_data["new_password2"])
            blog_user.save()
            return HttpResponseRedirect('/login/')
        else:
            return self.render_to_response({'form': form})


#swb: 校验找回密码邮箱，随后发送并缓存验证码。
class ForgetPasswordEmailCode(View):

    #swb: 校验找回密码邮箱，生成验证码并发送、缓存。
    def post(self, request: HttpRequest):
        """校验找回密码邮箱，生成并发送验证码，同时保存验证码供后续校验。"""
        # 只接受通过 ForgetPasswordCodeForm 校验的邮箱地址。
        form = ForgetPasswordCodeForm(request.POST)
        if not form.is_valid():
            return HttpResponse("错误的邮箱")
        to_email = form.cleaned_data["email"]

        # 生成验证码后发送给用户，并写入存储以便后续验证。
        code = generate_code()
        utils.send_verify_email(to_email, code)
        utils.set_code(to_email, code)

        return HttpResponse("ok")
