#swb: 说明自定义用户模型在管理后台使用的表单和列表配置。
# Django 表单、用户管理后台及相关字段组件。
from django import forms
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UsernameField
from django.utils.translation import gettext_lazy as _

# 自定义用户模型。
from .models import BlogUser


#swb: 校验管理员创建用户时两次输入的密码，并对密码进行哈希处理。
class BlogUserCreationForm(forms.ModelForm):
    """管理员创建用户时使用的表单，包含两次密码输入以确认密码。"""
    password1 = forms.CharField(label=_('password'), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Enter password again'), widget=forms.PasswordInput)

    class Meta:
        # 创建用户时，除密码字段外，表单直接收集邮箱。
        model = BlogUser
        fields = ('email',)

    #swb: 检查管理员输入的两次密码是否一致。
    def clean_password2(self):
        """校验两次输入的密码是否一致。"""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("passwords do not match"))
        return password2

    #swb: 保存前对密码进行哈希，并记录用户由管理后台创建。
    def save(self, commit=True):
        """以哈希形式保存密码；提交时标记用户来源为管理后台。"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.source = 'adminsite'
            user.save()
        return user


#swb: 配置管理后台编辑自定义用户时使用的表单。
class BlogUserChangeForm(UserChangeForm):
    """管理员编辑已有用户信息时使用的表单。"""
    class Meta:
        model = BlogUser
        fields = '__all__'
        # 用户名使用 Django 提供的专用字段类型。
        field_classes = {'username': UsernameField}

    #swb: 先初始化父类表单，再配置表单字段或控件。
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


#swb: 配置 Django 管理后台中的用户字段、排序和搜索方式。
class BlogUserAdmin(UserAdmin):
    """配置自定义用户模型在 Django 管理后台中的表单和列表展示。"""
    form = BlogUserChangeForm
    add_form = BlogUserCreationForm
    # 用户列表中展示的列及可点击进入详情页的列。
    list_display = (
        'id',
        'nickname',
        'username',
        'email',
        'last_login',
        'date_joined',
        'source')
    list_display_links = ('id', 'username')
    # 默认按用户 ID 倒序排列，并支持按用户名、昵称和邮箱搜索。
    ordering = ('-id',)
    search_fields = ('username', 'nickname', 'email')
