from django.contrib import admin

#zly: 后台管理入口（原注释：Register your models here.）。


#zly: CommandsAdmin：命令表后台展示配置。
class CommandsAdmin(admin.ModelAdmin):
    """命令模型后台管理配置类，用于在Django后台展示命令相关字段"""
    #zly: 列表页展示标题、命令内容、描述字段。
    list_display = ('title', 'command', 'describe')


#zly: EmailSendLogAdmin：邮件日志后台展示配置，禁止新增日志。
class EmailSendLogAdmin(admin.ModelAdmin):
    """邮件发送日志模型后台管理配置类，用于查看邮件发送记录，禁止新增日志"""
    #zly: 列表展示标题、收件邮箱、发送结果、创建时间。
    list_display = ('title', 'emailto', 'send_result', 'creation_time')
    #zly: 只读字段：日志内容不允许后台修改。
    readonly_fields = (
        'title',
        'emailto',
        'send_result',
        'creation_time',
        'content')

    #zly: 重写新增权限方法，禁止在后台手动添加邮件日志。
    def has_add_permission(self, request):
        """重写新增权限方法，禁止在后台手动添加邮件日志"""
        return False
