#zy: 模块精读：djangoblog 包入口。default_app_config 显式声明本应用使用的 AppConfig 类，属旧版 Django 写法；
#zy: 新版 Django 会自动发现 apps.py，此行可视为历史遗留（潜在清理点）。
# 旧版 Django 的 app 配置入口：声明本应用使用的 AppConfig 类（新版 Django 会自动发现 apps.py）
default_app_config = 'djangoblog.apps.DjangoblogAppConfig'
