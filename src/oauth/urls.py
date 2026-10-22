from django.urls import path

from . import views

# oauth 应用的命名空间，供模板标签与 reverse() 反向解析使用
app_name = "oauth"
# oauth 应用路由表：覆盖「发起授权 → 邮箱绑定 → 邮箱确认 → 绑定成功 → 授权回调」完整流程
urlpatterns = [
    path(
        r'oauth/authorize',
        views.authorize),  # OAuth 授权回调：接收 code 换取 token 并完成登录
    path(
        r'oauth/requireemail/<int:oauthid>.html',
        views.RequireEmailView.as_view(),
        name='require_email'),  # 引导用户填写绑定邮箱
    path(
        r'oauth/emailconfirm/<int:id>/<sign>.html',
        views.emailconfirm,
        name='email_confirm'),  # 邮箱确认链接：校验签名后完成绑定
    path(
        r'oauth/bindsuccess/<int:oauthid>.html',
        views.bindsuccess,
        name='bindsuccess'),  # 绑定成功 / 等待验证提示页
    path(
        r'oauth/oauthlogin',
        views.oauthlogin,
        name='oauthlogin')]  # 发起第三方 OAuth 登录
