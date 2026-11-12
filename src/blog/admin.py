#hzh: 本模块配置Django后台的文章、分类、标签及站点设置管理界面。
from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Register your models here.
from .models import Article, Category, Tag, Links, SideBar, BlogSettings
from djangoblog.utils import cache


# 文章后台编辑表单，使用 Article 模型的全部字段
class ArticleForm(forms.ModelForm):
    # body = forms.CharField(widget=AdminPagedownWidget())

    class Meta:
        model = Article
        fields = '__all__'


# 将后台批量选中的文章状态修改为已发布
#hzh: 批量发布直接更新数据库字段，不会逐个调用文章模型的save方法。
def makr_article_publish(modeladmin, request, queryset):
    # 第六周架构标注（黄梓涵）：后台 action 直接批量更新状态，与逐个调用
    # Article.save() 的流程不同；QuerySet.update() 不触发模型 save()/post_save。
    # 因而不能仅凭保存信号认定本 action 已完成缓存失效或搜索索引同步。
    queryset.update(status='p')


# 将后台批量选中的文章状态修改为草稿
def draft_article(modeladmin, request, queryset):
    queryset.update(status='d')


# 批量关闭选中文章的评论功能
def close_article_commentstatus(modeladmin, request, queryset):
    queryset.update(comment_status='c')


# 批量开启选中文章的评论功能
def open_article_commentstatus(modeladmin, request, queryset):
    queryset.update(comment_status='o')



#hzh: 置顶时生成高于当前最大排序值的优先级。
def _change_article_pin(queryset, pin):
    if pin:
        highest = Article.objects.aggregate(
            highest=Max('article_order')
        )['highest'] or 0
        target_order = max(highest, 0) + 1
    else:
        target_order = 0

    changed = queryset.exclude(
        article_order=target_order
    ).update(article_order=target_order)

    #hzh: 批量更新不会触发模型保存信号，主动清理缓存。
    if changed:
        cache.clear()

    return changed


@admin.action(description='置顶所选文章')
def pin_articles(modeladmin, request, queryset):
    changed = _change_article_pin(queryset, True)
    modeladmin.message_user(
        request, f'已置顶 {changed} 篇文章'
    )


@admin.action(description='取消置顶所选文章')
def unpin_articles(modeladmin, request, queryset):
    changed = _change_article_pin(queryset, False)
    modeladmin.message_user(
        request, f'已取消置顶 {changed} 篇文章'
    )


makr_article_publish.short_description = _('Publish selected articles')
draft_article.short_description = _('Draft selected articles')
close_article_commentstatus.short_description = _('Close article comments')
open_article_commentstatus.short_description = _('Open article comments')


# 文章后台管理配置，控制文章列表展示、筛选、搜索和批量操作
#hzh: 文章后台管理类集中配置列表字段、筛选条件、编辑表单和批量操作。
class ArticlelAdmin(admin.ModelAdmin):
    # 第六周架构标注（黄梓涵）：文章新增、编辑、删除由 Django ModelAdmin
    # 提供标准页面和权限检查；本类配置表单、筛选及 action，未定义前台 CRUD 视图。
    # get_form() 限制可选作者为超级用户，不等同于限制所有后台操作者必须是超级用户。
    list_per_page = 20
    search_fields = ('body', 'title')
    form = ArticleForm
    list_display = (
        'id',
        'title',
        'author',
        'link_to_category',
        'creation_time',
        'views',
        'status',
        'type',
        'article_order',
        'pin_toggle')
    list_display_links = ('id', 'title')
    list_filter = ('status', 'type', 'category')
    date_hierarchy = 'creation_time'
    filter_horizontal = ('tags',)
    exclude = ('creation_time', 'last_modify_time')
    view_on_site = True
    actions = [
        makr_article_publish,
        draft_article,
        close_article_commentstatus,
        open_article_commentstatus,
        pin_articles,
        unpin_articles]
    raw_id_fields = ('author', 'category',)


    @admin.display(description='置顶操作')
    def pin_toggle(self, obj):
        if obj.article_order > 0:
            return format_html(
                '<button type="submit" class="button" '
                'name="unpin_article_id" value="{}">取消置顶</button>',
                obj.pk
            )
        return format_html(
            '<button type="submit" class="button" '
            'name="pin_article_id" value="{}">置顶</button>',
            obj.pk
        )

    #hzh: 使用 POST 修改文章状态，并检查后台修改权限。
    def changelist_view(self, request, extra_context=None):
        pin_key = None
        if request.method == 'POST':
            if 'pin_article_id' in request.POST:
                pin_key = 'pin_article_id'
            elif 'unpin_article_id' in request.POST:
                pin_key = 'unpin_article_id'

        if pin_key is not None:
            if not self.has_change_permission(request):
                raise PermissionDenied

            obj = self.get_object(request, request.POST.get(pin_key))
            if obj is None:
                self.message_user(
                    request, '文章不存在或已删除',
                    level=messages.ERROR
                )
            elif not self.has_change_permission(request, obj):
                raise PermissionDenied
            else:
                pin = pin_key == 'pin_article_id'
                _change_article_pin(
                    Article.objects.filter(pk=obj.pk), pin
                )
                message = '置顶成功' if pin else '取消置顶成功'
                self.message_user(request, message)

            return HttpResponseRedirect(request.get_full_path())

        return super().changelist_view(request, extra_context)


    # 将分类名称显示为可点击链接，方便进入对应分类的后台编辑页
    def link_to_category(self, obj):
        info = (obj.category._meta.app_label, obj.category._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.category.id,))
        return format_html(u'<a href="%s">%s</a>' % (link, obj.category.name))

    link_to_category.short_description = _('category')

    # 编辑文章时只允许从超级用户中选择作者
    def get_form(self, request, obj=None, **kwargs):
        form = super(ArticlelAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['author'].queryset = get_user_model(
        ).objects.filter(is_superuser=True)
        return form

    def save_model(self, request, obj, form, change):
        # 第六周架构标注（黄梓涵）：委托父类保存模型；多对多 tags 的保存
        # 属于后台后续 save_related() 阶段，不能把全部表单关系都归到本方法。
        super(ArticlelAdmin, self).save_model(request, obj, form, change)

    def get_view_on_site_url(self, obj=None):
        if obj:
            url = obj.get_full_url()
            return url
        else:
            from djangoblog.utils import get_current_site
            site = get_current_site().domain
            return site


# 标签后台管理配置
class TagAdmin(admin.ModelAdmin):
    exclude = ('slug', 'last_mod_time', 'creation_time')


# 分类后台管理配置，显示父分类和排序信息
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_category', 'index')
    exclude = ('slug', 'last_mod_time', 'creation_time')


# 友情链接后台管理配置
class LinksAdmin(admin.ModelAdmin):
    exclude = ('last_mod_time', 'creation_time')


# 侧边栏后台管理配置
class SideBarAdmin(admin.ModelAdmin):
    list_display = ('name', 'content', 'is_enable', 'sequence')
    exclude = ('last_mod_time', 'creation_time')


class BlogSettingsAdmin(admin.ModelAdmin):
    """单例配置Admin - 直接跳转到编辑页面"""

    def has_add_permission(self, request):
        """如果已经存在配置，则禁止添加"""
        return not BlogSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """禁止删除配置"""
        return False

    def changelist_view(self, request, extra_context=None):
        """列表页直接跳转到编辑页面"""
        from django.http import HttpResponseRedirect
        obj = BlogSettings.objects.first()
        if obj:
            return HttpResponseRedirect(
                reverse('admin:blog_blogsettings_change', args=[obj.pk])
            )
        # 如果不存在配置，跳转到添加页面
        return HttpResponseRedirect(
            reverse('admin:blog_blogsettings_add')
        )

    def save_model(self, request, obj, form, change):
        """保存设置时清除缓存"""
        super().save_model(request, obj, form, change)
        # 确保缓存被清除
        from djangoblog.utils import cache
        cache.clear()
        self.message_user(request, '设置已保存，缓存已清除')
