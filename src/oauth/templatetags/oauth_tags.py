from django import template
from django.urls import reverse

from oauth.oauthmanager import get_oauth_apps

# 注册本模块为 Django 模板标签库
register = template.Library()


@register.inclusion_tag('oauth/oauth_applications.html')
def load_oauth_applications(request):
    """
    加载已启用的第三方登录入口列表的模板标签。
    渲染 oauth/oauth_applications.html，为登录页输出各平台（github/qq/weibo 等）的登录链接。
    """
    # 获取所有已启用的第三方平台配置
    applications = get_oauth_apps()
    if applications:
        # 反向解析 OAuth 登录入口 URL
        baseurl = reverse('oauth:oauthlogin')
        # 记录当前页面路径，登录成功后跳回原页面
        path = request.get_full_path()

        # 为每个平台生成 (图标名, 登录链接) 二元组，链接携带 type 与 next_url 参数
        apps = list(map(lambda x: (x.ICON_NAME, '{baseurl}?type={type}&next_url={next}'.format(
            baseurl=baseurl, type=x.ICON_NAME, next=path)), applications))
    else:
        # 无启用的平台时返回空列表，模板据此不渲染登录按钮
        apps = []
    return {
        'apps': apps
    }
