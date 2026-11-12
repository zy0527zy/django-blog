#zly: 模块说明：servermanager 邮件失败重试服务，基于 EmailSendLog 补发失败邮件。
"""
src/servermanager/services.py

邮件失败重试服务：
读取 EmailSendLog 中发送失败的记录，重新发送并更新日志（重试次数、最后重试时间、失败原因）。
只处理 servermanager 自己的数据与逻辑，不改动其他 app 的邮件发送代码。
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

#zly: 模块级日志记录器，重试失败时记录收件人与异常信息。
logger = logging.getLogger(__name__)


#zly: EmailService：统一处理失败邮件重试与发送日志更新。
class EmailService:
    """邮件失败重试服务：批量/单条重发失败邮件，并更新 EmailSendLog。"""

    #zly: retry_failed：批量重试失败邮件，返回（总数，成功数）。
    @classmethod
    def retry_failed(cls, queryset=None):
        """批量重试失败邮件，返回 (总数, 成功数)。"""
        #zly: 延迟导入模型，避免应用加载阶段产生循环依赖。
        from .models import EmailSendLog  # pylint: disable=import-outside-toplevel

        if queryset is None:
            queryset = EmailSendLog.objects.filter(send_result=False)
        total = queryset.count()
        success = 0
        for log in queryset:
            if cls.retry(log):
                success += 1
        return total, success

    #zly: retry：对一条失败日志重发一次，累加重试次数并记录最后重试时间。
    @classmethod
    def retry(cls, log):
        """对指定日志重发一次，返回是否发送成功。"""
        log.retry_count += 1
        log.last_retry_time = timezone.now()
        return cls._attempt(log)

    #zly: _attempt：执行一次 SMTP 发送，并把结果、失败原因写回日志。
    @classmethod
    def _attempt(cls, log):
        #zly: 收件人在模型中用逗号拼接保存，发送前拆回列表并过滤空值。
        emailto = [addr for addr in log.emailto.split(',') if addr]
        if not emailto:
            return cls._finish(log, False, '收件人为空')

        msg = EmailMultiAlternatives(
            log.title,
            log.content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=emailto,
        )
        #zly: 邮件正文按 HTML 发送，和历史行为保持一致。
        msg.content_subtype = 'html'
        try:
            if msg.send() > 0:
                return cls._finish(log, True, '')
            return cls._finish(log, False, '邮件服务返回 0 封发送成功')
        except Exception as exc:  # pylint: disable=broad-exception-caught
            #zly: 捕获所有发送异常，记录日志后返回失败，由调用方决定是否继续重试。
            logger.warning('邮件重试失败（收件人 %s）：%s', log.emailto, exc)
            return cls._finish(log, False, str(exc))

    #zly: _finish：更新发送结果并落库，返回是否成功。
    @classmethod
    def _finish(cls, log, success, error_message):
        log.send_result = success
        #zly: 成功时清空失败原因；失败原因截断到 1000 字，避免超长内容入库。
        log.error_message = '' if success else str(error_message)[:1000]
        log.save()
        return success
