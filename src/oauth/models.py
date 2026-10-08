# Create your models here.
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


class OAuthUser(models.Model):
    """
    第三方授权用户表
    存储从第三方平台获取的用户信息。与本地 BlogUser 是“可选绑定”（0..1）的关系。
    """
    # 可选绑定：允许为空（null=True, blank=True），表示用户仅在第三方授权，尚未绑定本地账号
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # 指向自定义的 BlogUser
        verbose_name=_('author'),
        blank=True,
        null=True,
        on_delete=models.CASCADE)
    
    # 第三方平台的唯一标识（如微信的 openid）
    openid = models.CharField(max_length=50)
    # 第三方平台的昵称
    nickname = models.CharField(max_length=50, verbose_name=_('nick name'))
    # 访问令牌，用于调用第三方接口（可为空）
    token = models.CharField(max_length=150, null=True, blank=True)
    # 用户头像链接（可为空）
    picture = models.CharField(max_length=350, blank=True, null=True)
    # 第三方平台类型（如 github, weibo 等）
    type = models.CharField(blank=False, null=False, max_length=50)
    # 第三方平台的邮箱（可为空）
    email = models.CharField(max_length=50, null=True, blank=True)
    # 存储第三方返回的原始元数据（可为空）
    metadata = models.TextField(null=True, blank=True)
    # 创建时间，默认当前时间
    creation_time = models.DateTimeField(_('creation time'), default=now)
    # 最后修改时间，默认当前时间
    last_modify_time = models.DateTimeField(_('last modify time'), default=now)

    def __str__(self):
        # 对象的字符串表示，返回第三方昵称
        return self.nickname

    class Meta:
        verbose_name = _('oauth user')
        verbose_name_plural = verbose_name
        # 默认按创建时间倒序排列
        ordering = ['-creation_time']


class OAuthConfig(models.Model):
    """
    第三方登录配置表
    存储各平台的 AppKey、AppSecret 及回调地址，供模板渲染登录按钮使用（oauth_applications）。
    """
    # 平台类型枚举，对应模板中渲染的不同第三方登录入口
    TYPE = (
        ('weibo', _('weibo')),
        ('google', _('google')),
        ('github', 'GitHub'),
        ('facebook', 'FaceBook'),
        ('qq', 'QQ'),
    )
    # 平台类型，默认为 'a'（注意：此默认值不在 TYPE 枚举中，建议根据实际需求修改）
    type = models.CharField(_('type'), max_length=10, choices=TYPE, default='a')
    # 平台申请的 AppKey
    appkey = models.CharField(max_length=200, verbose_name='AppKey')
    # 平台申请的 AppSecret
    appsecret = models.CharField(max_length=200, verbose_name='AppSecret')
    # OAuth 回调地址
    callback_url = models.CharField(
        max_length=200,
        verbose_name=_('callback url'),
        blank=False,
        default='')
    # 是否启用该平台登录（模板渲染时通过此字段过滤）
    is_enable = models.BooleanField(
        _('is enable'), default=True, blank=False, null=False)
    # 创建时间，默认当前时间
    creation_time = models.DateTimeField(_('creation time'), default=now)
    # 最后修改时间，默认当前时间
    last_modify_time = models.DateTimeField(_('last modify time'), default=now)

    def clean(self):
        # 校验：确保同一类型的平台配置只能存在一个（排除自身）
        if OAuthConfig.objects.filter(
                type=self.type).exclude(id=self.id).count():
            raise ValidationError(_(self.type + _('already exists')))

    def __str__(self):
        # 对象的字符串表示，返回平台类型
        return self.type

    class Meta:
        verbose_name = 'oauth配置'
        verbose_name_plural = verbose_name
        # 默认按创建时间倒序排列
        ordering = ['-creation_time']