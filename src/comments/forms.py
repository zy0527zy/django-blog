# =============================================================================
# comments 应用 · 表单定义（forms.py）
# -----------------------------------------------------------------------------
# 本文件定义评论发表时使用的表单：
#   CommentForm 继承 Django 的 ModelForm，基于 Comment 模型自动生成表单，
#   用户在前端只填写「正文 body」，而 parent_comment_id 是隐藏字段，
#   由前端在回复他人时自动带上（值为被回复的父评论 id），用户看不到。
# =============================================================================
from django import forms
from django.forms import ModelForm

from .models import Comment


class CommentForm(ModelForm):
    # 隐藏字段：父评论 id。普通评论为空；回复某条评论时前端自动填上被回复评论的 id
    # required=False 表示允许为空（顶层评论没有父评论）
    parent_comment_id = forms.IntegerField(
        widget=forms.HiddenInput, required=False)

    class Meta:
        # 表单对应的模型：Comment
        model = Comment
        # 只开放「正文」字段给用户填写，其他字段（作者/文章/父评论）由视图逻辑处理
        fields = ['body']
