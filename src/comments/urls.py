# =============================================================================
# comments 应用 · URL 路由配置（urls.py）
# -----------------------------------------------------------------------------
# 本文件定义 comments 应用对外暴露的两个 URL 地址，把请求分发给对应视图：
#   1. /article/<文章id>/postcomment  → CommentPostView    提交评论 / 回复
#   2. /comment/<评论id>/react        → CommentReactionView 评论 Emoji 反应
# 注意：app_name = "comments" 用于在模板/代码中按命名空间引用这些路由。
# =============================================================================
from django.urls import path

from . import views

app_name = "comments"
urlpatterns = [
    # 提交评论：POST 表单提交到该地址，携带文章 id，交给 CommentPostView 处理
    path(
        'article/<int:article_id>/postcomment',
        views.CommentPostView.as_view(),
        name='postcomment'),
    # 评论反应（点赞/表情）：GET 查数据、POST 切换反应，交给 CommentReactionView 处理
    path(
        'comment/<int:comment_id>/react',
        views.CommentReactionView.as_view(),
        name='comment_react'),
]
