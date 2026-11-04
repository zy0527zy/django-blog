#swb: 向 Django 注册 accounts 应用。
from django.apps import AppConfig


#swb: 向 Django 声明当前应用的包名。
class AccountsConfig(AppConfig):
    name = 'accounts'
