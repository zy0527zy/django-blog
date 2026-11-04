#swb: 扩展 Django 用户模型，增加博客资料和作者页面地址。
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from djangoblog.utils import get_current_site

# Create your models here.


#swb: 为 Django 用户记录增加博客资料和作者页面地址。
class BlogUser(AbstractUser):
    """站点用户模型，在 Django 默认用户字段基础上扩展博客资料。"""

    # 用户在博客页面展示的昵称；允许留空，未填写时可使用用户名。
    nickname = models.CharField(_('nick name'), max_length=100, blank=True)
    # 用户记录的创建时间和最后修改时间，默认取当前时间。
    creation_time = models.DateTimeField(_('creation time'), default=now)
    last_modify_time = models.DateTimeField(_('last modify time'), default=now)
    # 用户的创建来源，例如注册渠道；允许留空。
    source = models.CharField(_('create source'), max_length=100, blank=True)

    #swb: 返回该用户作者详情页的相对地址。
    def get_absolute_url(self):
        """返回该用户在博客中的作者详情页相对地址。"""
        return reverse(
            'blog:author_detail', kwargs={
                'author_name': self.username})

    #swb: 使用邮箱作为用户对象的可读字符串表示。
    def __str__(self):
        """以邮箱作为用户对象的可读字符串表示。"""
        return self.email

    #swb: 将站点域名与作者页面路径拼接为 HTTPS 地址。
    def get_full_url(self):
        """拼接当前站点域名和作者详情页路径，返回完整 HTTPS 地址。"""
        site = get_current_site().domain
        url = f"https://{site}{self.get_absolute_url()}"
        return url

    #swb: 模型元数据配置后台名称、默认排序及 latest() 使用的字段。
    class Meta:
        """配置用户记录的默认排序及后台显示名称。"""
        ordering = ['-id']
        verbose_name = _('user')
        verbose_name_plural = verbose_name
        get_latest_by = 'id'
