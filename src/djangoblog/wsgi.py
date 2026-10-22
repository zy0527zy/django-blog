"""
djangoblog 的 WSGI 配置

把 Django 应用以 WSGI 可调用对象 ``application`` 暴露出来，
供 uwsgi / gunicorn 等 Web 服务器在部署时调用。
"""

#zy: 模块精读：部署入口。关键点：DJANGO_SETTINGS_MODULE 必须在 get_wsgi_application() 之前设置，
#zy: 否则 Django 找不到配置模块会启动失败；application 是 WSGI 服务器与 Django 之间唯一的调用入口。

import os

from django.core.wsgi import get_wsgi_application

# 指定 Django 使用的配置文件模块（服务器启动前必须设置好）
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoblog.settings")

# 生成 WSGI 应用对象，作为 Web 服务器与 Django 之间的入口
application = get_wsgi_application()
