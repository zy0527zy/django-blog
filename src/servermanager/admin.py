#zly: 模块说明：servermanager 后台管理配置，提供命令与邮件日志的展示、失败邮件重试操作。
from django.contrib import admin

from .services import EmailService

#zly: 后台管理入口（原注释：Register your models here.）。


#zly: CommandsAdmin：命令表后台展示配置。
class CommandsAdmin(admin.ModelAdmin):
    """命令模型后台管理配置类，用于在Django后台展示命令相关字段"""
    #zly: 列表页展示标题、命令内容、描述字段。
    list_display = ('title', 'command', 'describe')


#zly: EmailSendLogAdmin：邮件日志后台展示配置，禁止新增日志，支持重试失败邮件。
class EmailSendLogAdmin(admin.ModelAdmin):
    """邮件发送日志模型后台管理配置类，用于查看邮件发送记录，禁止手动新增日志"""
    #zly: 列表展示标题、收件邮箱、发送结果、重试次数与时间。
    list_display = (
        'title',
        'emailto',
        'send_result',
        'retry_count',
        'last_retry_time',
        'creation_time')
    #zly: 支持按发送结果筛选，快速找出失败邮件。
    list_filter = ('send_result',)
    #zly: 支持按收件人和标题搜索。
    search_fields = ('emailto', 'title')
    #zly: 只读字段：日志内容与重试信息不允许后台修改。
    readonly_fields = (
        'title',
        'emailto',
        'send_result',
        'content',
        'retry_count',
        'last_retry_time',
        'error_message',
        'creation_time')
    #zly: 注册自定义操作：重试选中的失败邮件。
    actions = ('retry_failed',)

    #zly: 重写新增权限方法，禁止在后台手动添加邮件日志。
    def has_add_permission(self, request):
        """重写新增权限方法，禁止在后台手动添加邮件日志"""
        return False

    #zly: 后台操作：对选中的失败邮件逐条重发，并统计成功数量。
    @admin.action(description='重试发送选中的失败邮件')
    def retry_failed(self, request, queryset):
        """重试选中的失败邮件，成功则更新发送结果与重试次数"""
        total, success = EmailService.retry_failed(
            queryset.filter(send_result=False))
        self.message_user(
            request,
            f'共重试 {total} 封失败邮件，成功 {success} 封。')
