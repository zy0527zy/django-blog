"""支持使用用户名或邮箱地址进行登录的认证后端。"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameModelBackend(ModelBackend):
    """
    允许使用用户名或邮箱登录
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """根据输入内容查询用户，并在密码验证通过后返回用户对象。"""
        # 含有 @ 时按邮箱查找，否则按用户名查找。
        if '@' in username:
            kwargs = {'email': username}
        else:
            kwargs = {'username': username}
        try:
            user = get_user_model().objects.get(**kwargs)
            # 使用 Django 用户模型的密码校验方法验证哈希密码。
            if user.check_password(password):
                return user
        except get_user_model().DoesNotExist:
            # 未找到对应账号时，认证失败。
            return None

    def get_user(self, username):
        """根据用户主键获取用户，供 Django 会话认证流程调用。"""
        try:
            return get_user_model().objects.get(pk=username)
        except get_user_model().DoesNotExist:
            return None
