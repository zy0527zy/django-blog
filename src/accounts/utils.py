"""账号邮箱验证码的发送、缓存和校验工具。"""
#swb: 发送、缓存并校验账户验证码。
from datetime import timedelta

from django.core.cache import cache
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from djangoblog.utils import send_email

# 验证码在缓存中的有效期为五分钟。
#swb: 统一设置验证码在缓存中的有效时长。
_code_ttl = timedelta(minutes=5)


#swb: 构造验证码邮件，并调用公共邮件工具发送。
def send_verify_email(to_mail: str, code: str, subject: str = _("Verify Email")):
    """向指定邮箱发送验证码邮件（邮件正文用于密码重置场景）。
    Args:
        to_mail: 接受邮箱
        subject: 邮件主题
        code: 验证码
    """
    html_content = _(
        "You are resetting the password, the verification code is：%(code)s, valid within 5 minutes, please keep it "
        "properly") % {'code': code}
    send_email([to_mail], subject, html_content)


#swb: 将用户提交的验证码与缓存值比较，不匹配时返回错误。
def verify(email: str, code: str) -> str | None:
    """比较用户提交的验证码与缓存值，错误时返回提示文本。
    Args:
        email: 请求邮箱
        code: 验证码
    Return:
        如果有错误就返回错误str
    Node:
        这里的错误处理不太合理，应该采用raise抛出
        否测调用方也需要对error进行处理
    """
    cache_code = get_code(email)
    #swb: 仅当提交的验证码与缓存值不一致时返回错误。
    if cache_code != code:
        return gettext("Verification code error")


#swb: 将验证码写入缓存，并设置五分钟有效期。
def set_code(email: str, code: str):
    """将邮箱对应的验证码写入缓存，并设置过期时间。"""
    cache.set(email, code, _code_ttl.seconds)


#swb: 读取邮箱对应的缓存验证码；验证码不存在或过期时返回 None。
def get_code(email: str) -> str | None:
    """从缓存中读取邮箱对应的验证码；不存在或过期时返回 None。"""
    return cache.get(email)
