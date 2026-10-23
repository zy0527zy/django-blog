#xcz: 定义第三方登录补充邮箱时使用的表单及控件。
from django.contrib.auth.forms import forms
from django.forms import widgets


#xcz: 收集第三方平台未返回时用户补充的邮箱和待绑定账户编号。
class RequireEmailForm(forms.Form):
    """
    第三方登录绑定邮箱表单。
    当第三方平台未返回用户邮箱时，引导用户手动填写邮箱，用于后续本地账号的绑定。
    """
    # 邮箱输入框（必填），用于接收用户填写的绑定邮箱
    email = forms.EmailField(label='电子邮箱', required=True)
    # 隐藏字段，携带当前待绑定的 OAuthUser 主键 id，随表单一起提交
    oauthid = forms.IntegerField(widget=forms.HiddenInput, required=False)

    #xcz: 初始化表单控件或平台令牌状态。
    def __init__(self, *args, **kwargs):
        """初始化表单：为邮箱输入框设置占位提示与 Bootstrap 样式。"""
        super().__init__(*args, **kwargs)
        # 定制邮箱输入框的占位符和 CSS class，使其与页面风格统一
        self.fields['email'].widget = widgets.EmailInput(
            attrs={'placeholder': "email", "class": "form-control"})
