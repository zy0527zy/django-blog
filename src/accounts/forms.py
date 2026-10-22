#swb: 定义账户表单，并校验登录、注册和密码找回输入。
from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import widgets
from django.utils.translation import gettext_lazy as _

from . import utils
from .models import BlogUser


#swb: 复用 Django 的认证校验逻辑，并定制登录控件。
class LoginForm(AuthenticationForm):
    """登录表单：沿用 Django 的认证校验，仅定制输入框外观。"""

    #swb: 先初始化父类表单，再配置表单字段或控件。
    def __init__(self, *args, **kwargs):
        # 保留父类对用户名、密码和认证状态的处理，再设置模板所需的控件属性。
        super().__init__(*args, **kwargs)
        # 使用普通文本框输入用户名，并附加前端样式和占位提示。
        self.fields['username'].widget = widgets.TextInput(
            attrs={'placeholder': "username", "class": "form-control"})
        # 密码控件会遮蔽输入内容，避免在页面上直接显示密码。
        self.fields['password'].widget = widgets.PasswordInput(
            attrs={'placeholder': "password", "class": "form-control"})


#swb: 复用 Django 的注册校验逻辑，并要求邮箱地址唯一。
class RegisterForm(UserCreationForm):
    """注册表单：复用 Django 用户创建和密码校验逻辑，并要求邮箱唯一。"""

    #swb: 先初始化父类表单，再配置表单字段或控件。
    def __init__(self, *args, **kwargs):
        # 初始化父类字段，包括用户名、邮箱和两次密码输入。
        super().__init__(*args, **kwargs)

        # 定制各字段控件的 HTML 类型、占位提示和统一表单样式。
        self.fields['username'].widget = widgets.TextInput(
            attrs={'placeholder': "username", "class": "form-control"})
        self.fields['email'].widget = widgets.EmailInput(
            attrs={'placeholder': "email", "class": "form-control"})
        self.fields['password1'].widget = widgets.PasswordInput(
            attrs={'placeholder': "password", "class": "form-control"})
        self.fields['password2'].widget = widgets.PasswordInput(
            attrs={'placeholder': "repeat password", "class": "form-control"})

    #swb: 检查邮箱是否符合当前表单对账户邮箱的要求。
    def clean_email(self):
        """校验邮箱尚未被其他用户使用；返回值会进入 cleaned_data。"""
        email = self.cleaned_data['email']
        # 邮箱地址在本系统中用作唯一注册标识之一，重复时阻止提交。
        #swb: 注册邮箱必须唯一，便于后续通过邮箱定位账户。
        if get_user_model().objects.filter(email=email).exists():
            raise ValidationError(_("email already exists"))
        return email

    class Meta:
        # UserCreationForm 根据此配置绑定用户模型，并将用户名和邮箱纳入表单。
        model = get_user_model()
        fields = ("username", "email")


#swb: 校验新密码、账户邮箱和找回验证码。
class ForgetPasswordForm(forms.Form):
    """找回密码表单：收集新密码、邮箱和邮箱验证码并逐项验证。"""

    # 新密码字段使用密码输入框，前端显示时不暴露明文。
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                'placeholder': _("New password")
            }
        ),
    )

    # 再次输入新密码，用于确认两次输入一致。
    new_password2 = forms.CharField(
        label="确认密码",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                'placeholder': _("Confirm password")
            }
        ),
    )

    # 接收账户邮箱，EmailField 会先检查输入是否符合邮箱格式。
    email = forms.EmailField(
        label='邮箱',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': _("Email")
            }
        ),
    )

    # 用户通过邮件收到的验证码；具体有效性在 clean_code 中检查。
    code = forms.CharField(
        label=_('Code'),
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': _("Code")
            }
        ),
    )

    #swb: 检查两次新密码是否一致，并调用 Django 密码校验器。
    def clean_new_password2(self):
        """检查两次新密码一致，并调用 Django 配置的密码强度验证器。"""
        # 从原始提交数据读取两次输入；clean_new_password2 在字段级校验时运行。
        password1 = self.data.get("new_password1")
        password2 = self.data.get("new_password2")
        # 仅当两项都已填写时比较，缺失值由字段自身的必填校验处理。
        if password1 and password2 and password1 != password2:
            raise ValidationError(_("passwords do not match"))
        # 使用项目配置的 Django 密码验证器检查强度及其他密码策略。
        #swb: 除检查两次密码一致外，也应用项目配置的密码策略。
        password_validation.validate_password(password2)

        return password2

    #swb: 检查邮箱是否符合当前表单对账户邮箱的要求。
    def clean_email(self):
        """确认邮箱对应现有账户，避免对未注册邮箱继续执行密码重置。"""
        user_email = self.cleaned_data.get("email")
        # 只接受用户表中已登记的邮箱；错误时不泄露以外的信息由提示策略决定。
        #swb: 只有已注册账户的邮箱才能继续密码找回流程。
        if not BlogUser.objects.filter(
                email=user_email
        ).exists():
            # todo 这里的报错提示可以判断一个邮箱是不是注册过，如果不想暴露可以修改
            raise ValidationError(_("email does not exist"))
        return user_email

    #swb: 校验验证码是否属于提交的邮箱地址。
    def clean_code(self):
        """使用邮箱和验证码调用账户工具进行验证；无效时将错误反馈给表单。"""
        code = self.cleaned_data.get("code")
        # verify 会检查该邮箱对应的验证码，并返回错误信息或空值。
        #swb: 验证码与对应邮箱一并校验，避免在不同账户间复用。
        error = utils.verify(
            email=self.cleaned_data.get("email"),
            code=code,
        )
        if error:
            raise ValidationError(error)
        return code


#swb: 校验申请找回验证码时提交的邮箱地址。
class ForgetPasswordCodeForm(forms.Form):
    """发送找回密码验证码时使用的轻量表单，只接收并格式校验邮箱。"""

    # EmailField 在验证码发送前检查邮箱输入格式。
    email = forms.EmailField(
        label=_('Email'),
    )
