from django import template
from django.urls import reverse

from oauth.oauthmanager import get_oauth_apps

#xcz: 为模板生成已启用平台的登录图标和跳转链接。
# 注册本模块为 Django 模板标签库
register = template.Library()


#xcz: 为模板生成已启用平台的登录图标和跳转链接。
@register.inclusion_tag('oauth/oauth_applications.html')
def load_oauth_applications(request):
    """
    加载已启用的第三方登录入口列表的模板标签。
    渲染 oauth/oauth_applications.html，为登录页输出各平台（github/qq/weibo 等）的登录链接。
    """
    # 获取所有已启用的第三方平台配置
    applications = get_oauth_apps()
    #xcz: 仅在有启用平台时生成入口，空列表会让模板不显示登录按钮。
    if applications:
        # 反向解析 OAuth 登录入口 URL
        baseurl = reverse('oauth:oauthlogin')
        # 记录当前页面路径，登录成功后跳回原页面
        path = request.get_full_path()

        # 为每个平台生成 (图标名, 登录链接) 二元组，链接携带 type 与 next_url 参数
        apps = [
            (app.ICON_NAME, f'{baseurl}?type={app.ICON_NAME}&next_url={path}')
            for app in applications
        ]
    else:
        # 无启用的平台时返回空列表，模板据此不渲染登录按钮
        apps = []
    return {
        'apps': apps
    }
