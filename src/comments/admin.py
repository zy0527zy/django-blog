# =============================================================================
# comments 应用 · Django 后台管理配置（admin.py）
# -----------------------------------------------------------------------------
# 本文件用于配置 Django 自带后台（/admin/）中「评论」「评论反应」两个模型的
# 列表展示、筛选、搜索、批量操作等管理功能，方便管理员在后台审核评论。
# 对应模型：Comment（评论）、CommentReaction（评论 Emoji 反应）。
# =============================================================================
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Comment, CommentReaction


def disable_commentstatus(modeladmin, request, queryset):
    """后台批量操作：将选中的评论设为不可展示（is_enable=False，隐藏评论）。"""
    queryset.update(is_enable=False)


def enable_commentstatus(modeladmin, request, queryset):
    """后台批量操作：将选中的评论设为可展示（is_enable=True，通过审核）。"""
    queryset.update(is_enable=True)


# 给两个批量操作函数设置后台下拉菜单里显示的中文/英文说明
disable_commentstatus.short_description = _('Disable comments')
enable_commentstatus.short_description = _('Enable comments')


class CommentAdmin(admin.ModelAdmin):
    """评论模型的后台管理配置。"""

    # 后台列表每页显示 20 条
    list_per_page = 20
    # 列表页展示的列：id、正文、作者、所属文章、是否展示、创建时间
    list_display = (
        'id',
        'body',
        'link_to_userinfo',
        'link_to_article',
        'is_enable',
        'creation_time')
    # 列表页可点击跳转编辑的列
    list_display_links = ('id', 'body', 'is_enable')
    # 右侧筛选器：按是否展示筛选
    list_filter = ('is_enable',)
    # 编辑页隐藏创建/修改时间字段（由系统自动维护）
    exclude = ('creation_time', 'last_modify_time')
    # 下拉框里可选的批量操作：禁用 / 启用评论
    actions = [disable_commentstatus, enable_commentstatus]
    # 外键字段用原始 id 输入框（避免下拉加载大量作者/文章）
    raw_id_fields = ('author', 'article')
    # 支持按正文内容搜索
    search_fields = ('body',)

    def link_to_userinfo(self, obj):
        """自定义列：把评论作者渲染成可点击的后台编辑链接。"""
        # 根据作者所在 app 和模型名，反向生成后台编辑地址
        info = (obj.author._meta.app_label, obj.author._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.author.id,))
        # 返回带 <a> 链接的 HTML，优先显示昵称，没有则显示邮箱
        return format_html(
            u'<a href="%s">%s</a>' %
            (link, obj.author.nickname if obj.author.nickname else obj.author.email))

    def link_to_article(self, obj):
        """自定义列：把评论所属文章渲染成可点击的后台编辑链接。"""
        info = (obj.article._meta.app_label, obj.article._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.article.id,))
        return format_html(
            u'<a href="%s">%s</a>' % (link, obj.article.title))

    # 两个自定义列的列头说明
    link_to_userinfo.short_description = _('User')
    link_to_article.short_description = _('Article')


class CommentReactionAdmin(admin.ModelAdmin):
    """评论 Emoji 反应模型的后台管理配置。"""

    # 列表页展示的列：id、表情、被点评论、点赞用户、时间
    list_display = ('id', 'reaction_type', 'link_to_comment', 'link_to_user', 'created_at')
    list_display_links = ('id', 'reaction_type')
    # 右侧筛选器：按表情类型、创建时间筛选
    list_filter = ('reaction_type', 'created_at')
    # 外键字段用原始 id 输入框
    raw_id_fields = ('comment', 'user')
    # 支持按评论正文、用户名搜索
    search_fields = ('comment__body', 'user__username')
    # 列表页顶部按时间分层浏览（年/月/日）
    date_hierarchy = 'created_at'

    def link_to_comment(self, obj):
        """自定义列：把被反应的评论渲染成可点击的后台编辑链接。"""
        info = (obj.comment._meta.app_label, obj.comment._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.comment.id,))
        return format_html(
            u'<a href="%s">Comment #%s</a>' % (link, obj.comment.id))

    def link_to_user(self, obj):
        """自定义列：把点赞用户渲染成可点击的后台编辑链接。"""
        info = (obj.user._meta.app_label, obj.user._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.user.id,))
        return format_html(
            u'<a href="%s">%s</a>' %
            (link, obj.user.nickname if obj.user.nickname else obj.user.username))

    # 两个自定义列的列头说明
    link_to_comment.short_description = _('Comment')
    link_to_user.short_description = _('User')


# 将两个模型注册到 Django 后台，并绑定上面的管理配置
admin.site.register(Comment, CommentAdmin)
admin.site.register(CommentReaction, CommentReactionAdmin)
