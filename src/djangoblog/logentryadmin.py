"""
Django 后台「操作日志」管理界面定制

自定义 django.contrib.admin 的 LogEntry 展示，让后台的"最近动作 / 操作日志"列表更易读：
- 把"被操作对象"和"操作用户"渲染成可点击的链接，方便跳转定位；
- 将日志设为只读（不允许新增、删除，修改也只允许只读查看），保证操作记录可追溯、不可篡改。
"""
from django.contrib import admin
from django.contrib.admin.models import DELETION
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse, NoReverseMatch
from django.utils.encoding import force_str
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class LogEntryAdmin(admin.ModelAdmin):
    """后台操作日志（LogEntry）的自定义管理类：只读展示，操作对象 / 用户做成可点击链接。"""

    # 右侧筛选器：按内容类型（即被操作的模型）筛选日志
    list_filter = [
        'content_type'
    ]

    # 搜索框：可按"对象名"或"变更信息"搜索
    search_fields = [
        'object_repr',
        'change_message'
    ]

    # 列表中可点击进入详情页的字段
    list_display_links = [
        'action_time',
        'get_change_message',
    ]

    # 列表展示的列
    list_display = [
        'action_time',          # 操作时间
        'user_link',            # 操作用户（可点击链接）
        'content_type',         # 被操作对象的类型
        'object_link',          # 被操作对象（可点击链接）
        'get_change_message',   # 变更说明
    ]

    def has_add_permission(self, request):
        """禁止在后台新增日志条目（日志由系统自动记录，无需手工添加）"""
        return False

    def has_change_permission(self, request, obj=None):
        """仅允许超级用户或有权限者"只读查看"日志；POST 提交一律禁止，防止篡改"""
        return (
                request.user.is_superuser or
                request.user.has_perm('admin.change_logentry')
        ) and request.method != 'POST'

    def has_delete_permission(self, request, obj=None):
        """禁止删除日志条目，保证操作记录可追溯"""
        return False

    def object_link(self, obj):
        """把"被操作对象"渲染成指向其后台编辑页的链接；对象已被删除时仅显示文本"""
        object_link = escape(obj.object_repr)
        content_type = obj.content_type

        if obj.action_flag != DELETION and content_type is not None:
            # 非"删除"操作且能拿到对象类型时，尝试生成可点击链接
            try:
                url = reverse(
                    'admin:{}_{}_change'.format(content_type.app_label,
                                                content_type.model),
                    args=[obj.object_id]
                )
                object_link = '<a href="{}">{}</a>'.format(url, object_link)
            except NoReverseMatch:
                # 该模型没有对应的后台编辑页，降级为纯文本
                pass
        return mark_safe(object_link)

    # 允许按对象名排序
    object_link.admin_order_field = 'object_repr'
    object_link.short_description = _('object')

    def user_link(self, obj):
        """把"操作用户"渲染成指向其后台编辑页的链接"""
        content_type = ContentType.objects.get_for_model(type(obj.user))
        user_link = escape(force_str(obj.user))
        try:
            # 尝试生成指向用户编辑页的链接
            url = reverse(
                'admin:{}_{}_change'.format(content_type.app_label,
                                            content_type.model),
                args=[obj.user.pk]
            )
            user_link = '<a href="{}">{}</a>'.format(url, user_link)
        except NoReverseMatch:
            pass
        return mark_safe(user_link)

    user_link.admin_order_field = 'user'
    user_link.short_description = _('user')

    def get_queryset(self, request):
        """预加载 content_type 关联，避免列表页 N+1 查询"""
        queryset = super(LogEntryAdmin, self).get_queryset(request)
        return queryset.prefetch_related('content_type')

    def get_actions(self, request):
        """移除"批量删除"动作，防止通过后台批量删掉操作日志"""
        actions = super(LogEntryAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
