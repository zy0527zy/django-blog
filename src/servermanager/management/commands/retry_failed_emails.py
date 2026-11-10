#zly: 管理命令说明：批量重试 EmailSendLog 中发送失败的邮件，可配合 cron 定时补发。
"""
src/servermanager/management/commands/retry_failed_emails.py

管理命令：重试 EmailSendLog 中 send_result=False 的邮件。
用法：
    python manage.py retry_failed_emails            # 重试全部失败邮件
    python manage.py retry_failed_emails --limit 10 # 最多重试 10 封
"""
from django.core.management.base import BaseCommand

from servermanager.models import EmailSendLog
from servermanager.services import EmailService


#zly: RetryFailedEmailsCommand：遍历失败日志逐条重发，并输出成功数量。
class Command(BaseCommand):
    #zly: 命令帮助信息，manage.py help 时展示。
    help = '重试发送 EmailSendLog 中发送失败的邮件'

    #zly: 支持 --limit 参数控制单次最多重试多少封，避免一次性重发过多。
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='最多重试的邮件数，0 表示全部')

    #zly: handle：按创建时间顺序取失败邮件，交给 EmailService 重试。
    def handle(self, *args, **options):
        queryset = EmailSendLog.objects.filter(
            send_result=False).order_by('creation_time')
        limit = options['limit']
        if limit > 0:
            queryset = queryset[:limit]

        total, success = EmailService.retry_failed(queryset)
        self.stdout.write(
            self.style.SUCCESS(f'共重试 {total} 封失败邮件，成功 {success} 封。'))
