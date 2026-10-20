#!/usr/bin/env python

"""
Django Blog 统一错误处理视图
提供统一的错误页面渲染，减少重复代码
"""

#zy: 模块精读：把 404/500/403/400 错误统一收敛到 render_error_page 一个函数，统一日志记录与页面渲染，避免重复写渲染逻辑（DRY）。
#zy: 注意：各处理器虽保留 template_name 形参（兼容 Django 签名），但实际模板在 render_error_page 里硬编码为 blog/error_page.html，形参未被使用。

import logging

from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def render_error_page(request, status_code, message, exception=None):
    """
    通用错误页面渲染函数

    统一处理各种 HTTP 错误，提供一致的错误页面展示

    Args:
        request: HTTP 请求对象
        status_code: HTTP 状态码（404, 403, 500等）
        message: 错误消息（支持国际化）
        exception: 异常对象（可选），会被记录到日志

    Returns:
        HttpResponse: 渲染后的错误页面

    Usage:
        def my_error_handler(request, exception):
            return render_error_page(request, 404, "Page not found", exception)
    """
    if exception:
        logger.error(
            f'HTTP {status_code} Error: {exception}',
            exc_info=True,
            extra={
                'request': request,
                'status_code': status_code
            }
        )

    return render(
        request,
        'blog/error_page.html',
        {
            'message': message,
            'statuscode': str(status_code)
        },
        status=status_code
    )


def page_not_found_view(request, exception, template_name='blog/error_page.html'):
    """
    404 错误页面处理器

    当用户访问不存在的页面时显示

    Args:
        request: HTTP 请求对象
        exception: 异常对象
        template_name: 模板名称（保留参数以兼容 Django 标准）

    Returns:
        HttpResponse: 404 错误页面
    """
    return render_error_page(
        request,
        404,
        _('Sorry, the page you requested is not found, please click the home page to see other?'),
        exception
    )


def server_error_view(request, template_name='blog/error_page.html'):
    """
    500 错误页面处理器

    当服务器内部错误时显示

    Args:
        request: HTTP 请求对象
        template_name: 模板名称（保留参数以兼容 Django 标准）

    Returns:
        HttpResponse: 500 错误页面
    """
    return render_error_page(
        request,
        500,
        _('Sorry, the server is busy, please click the home page to see other?')
    )


def permission_denied_view(request, exception, template_name='blog/error_page.html'):
    """
    403 错误页面处理器

    当用户无权限访问时显示

    Args:
        request: HTTP 请求对象
        exception: 异常对象
        template_name: 模板名称（保留参数以兼容 Django 标准）

    Returns:
        HttpResponse: 403 错误页面
    """
    return render_error_page(
        request,
        403,
        _('Sorry, you do not have permission to access this page?'),
        exception
    )


def bad_request_view(request, exception, template_name='blog/error_page.html'):
    """
    400 错误页面处理器

    当请求格式错误时显示

    Args:
        request: HTTP 请求对象
        exception: 异常对象
        template_name: 模板名称（保留参数以兼容 Django 标准）

    Returns:
        HttpResponse: 400 错误页面
    """
    return render_error_page(
        request,
        400,
        _('Sorry, the request was invalid?'),
        exception
    )
