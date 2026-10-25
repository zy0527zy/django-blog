#xcz: 配置 OAuth 用户和平台配置在 Django 管理后台中的展示与权限。
import logging

from django.contrib import admin

# Register your models here.
from django.urls import reverse
from django.utils.html import format_html

logger = logging.getLogger(__name__)


#xcz: 配置第三方用户在管理后台的只读展示、搜索和筛选行为。
class OAuthUserAdmin(admin.ModelAdmin):
    """
    第三方授权用户（OAuthUser）的后台管理界面配置。
    第三方用户数据由 OAuth 登录流程自动写入，后台只读展示、禁止手动新增。
    """
    # 可按昵称、邮箱搜索
    search_fields = ('nickname', 'email')
    # 每页显示 20 条
    list_per_page = 20
    # 列表页展示的字段
    list_display = (
        'id',
        'nickname',
        'link_to_usermodel',
        'show_user_image',
        'type',
        'email',
    )
    # id、昵称可点击进入详情
    list_display_links = ('id', 'nickname')
    # 可按绑定的本地用户、平台类型筛选
    list_filter = ('author', 'type',)
    # 只读字段（其余全部字段在 get_readonly_fields 中动态补齐）
    readonly_fields = []

    #xcz: 汇总后台只读字段，限制对 OAuth 记录的手动修改。
    def get_readonly_fields(self, request, obj=None):
        """返回只读字段集合：除声明的只读字段外，其余全部字段均设为只读，实现后台只读。"""
        model_fields = obj._meta.fields + obj._meta.many_to_many
        return list(self.readonly_fields) + [field.name for field in model_fields]

    #xcz: 禁止管理员手动创建第三方授权用户。
    def has_add_permission(self, request):
        """禁止在后台手动新增第三方授权用户（数据只能由 OAuth 登录流程写入）。"""
        return False

    #xcz: 生成跳转到关联本地用户管理页的链接。
    def link_to_usermodel(self, obj):
        """列表页展示「绑定的本地用户」列：生成指向本地用户详情页的可点击链接。"""
        if obj.author:
            info = (obj.author._meta.app_label, obj.author._meta.model_name)
            link = reverse(f'admin:{info[0]}_{info[1]}_change', args=(obj.author.id,))
            display_name = obj.author.nickname or obj.author.email
            return format_html(
                '<a href="{}">{}</a>', link, display_name)

    #xcz: 在管理列表中渲染第三方用户头像。
    def show_user_image(self, obj):
        """列表页展示「用户头像」列：渲染第三方头像缩略图。"""
        img = obj.picture
        return format_html('<img src="{}" style="width:50px;height:50px">', img)

    # 自定义列的中文表头
    link_to_usermodel.short_description = '用户'
    show_user_image.short_description = '用户头像'


#xcz: 配置第三方平台登录参数在管理后台的展示方式。
class OAuthConfigAdmin(admin.ModelAdmin):
    """
    第三方登录配置（OAuthConfig）的后台管理界面配置。
    用于维护各平台（weibo/google/github/facebook/qq）的 AppKey、AppSecret 与启用状态。
    """
    # 列表页展示的字段
    list_display = ('type', 'appkey', 'appsecret', 'is_enable')
    # 可按平台类型筛选
    list_filter = ('type',)
