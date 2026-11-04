#zly: 模块说明：servermanager 页面视图，提供站点数据统计面板（仅超级管理员可访问）。
"""
servermanager 应用视图文件
功能：提供站点数据统计面板，权限与自定义后台保持一致（仅超级管理员）。
"""
#zly: 页面视图入口：目前提供站点数据统计面板。
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from .statistics import SiteStatisticsService


#zly: 站点数据统计面板：未登录跳转登录页，非超级管理员返回 403。
@login_required
def site_statistics(request):
    """渲染站点数据统计面板。"""
    if not request.user.is_superuser:
        raise PermissionDenied('仅超级管理员可以查看站点数据统计')

    stats = SiteStatisticsService().collect()
    return render(
        request,
        'servermanager/statistics.html',
        {'stats': stats, 'title': '站点数据统计'})
