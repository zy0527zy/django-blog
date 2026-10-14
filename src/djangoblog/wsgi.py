"""
djangoblog 的 WSGI 配置

把 Django 应用以 WSGI 可调用对象 ``application`` 暴露出来，
供 uwsgi / gunicorn 等 Web 服务器在部署时调用。
"""

import os

from django.core.wsgi import get_wsgi_application

# 指定 Django 使用的配置文件模块（服务器启动前必须设置好）
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoblog.settings")

# 生成 WSGI 应用对象，作为 Web 服务器与 Django 之间的入口
application = get_wsgi_application()
