from django.contrib import admin
# Register your models here.

"""命令模型后台管理配置类，用于在Django后台展示命令相关字段"""
class CommandsAdmin(admin.ModelAdmin):
    # 后台列表页展示标题、命令内容、描述字段
    list_display = ('title', 'command', 'describe')

"""邮件发送日志模型后台管理配置类，用于查看邮件发送记录，禁止新增日志"""
class EmailSendLogAdmin(admin.ModelAdmin):
    # 后台列表展示标题、收件邮箱、发送结果、创建时间
    list_display = ('title', 'emailto', 'send_result', 'creation_time')
    # 设置只读字段，日志内容不允许后台修改
    readonly_fields = (
        'title',
        'emailto',
        'send_result',
        'creation_time',
        'content')

    """重写新增权限方法，禁止在后台手动添加邮件日志"""
    def has_add_permission(self, request):
        return False
