# =============================================================================
# comments 应用 · 视图（MVT 中的 V 层）
# -----------------------------------------------------------------------------
# 本文件包含两个类视图，分别处理评论相关的两类请求：
#   1. CommentPostView    提交评论（表单方式，需要登录）
#   2. CommentReactionView 评论的 Emoji 反应 / 点赞（JSON 接口，GET 公开 / POST 需登录）
# 评论区片段由文章详情页 include 进来，表单提交后再重定向回文章详情页。
# =============================================================================
# Create your views here.
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from accounts.models import BlogUser
from blog.models import Article
from djangoblog.base_views import AuthenticatedFormView
from .forms import CommentForm
from .models import Comment, CommentReaction


class CommentPostView(AuthenticatedFormView):
    """
    评论提交视图（处理发表评论 / 回复）

    使用 AuthenticatedFormView 基类，自动提供：
    - 登录验证（未登录用户会被重定向到登录页）
    - CSRF 保护
    """
    form_class = CommentForm
    # 表单校验失败时，回退到文章详情页重新渲染
    template_name = 'blog/article_detail.html'

    def get(self, request, *args, **kwargs):
        """处理 GET 请求：直接访问提交地址时，重定向回文章详情的评论区。"""
        article_id = self.kwargs['article_id']
        article = get_object_or_404(Article, pk=article_id)
        url = article.get_absolute_url()
        # 带 #comments 锚点，定位到评论区
        return HttpResponseRedirect(url + "#comments")

    def form_invalid(self, form):
        """表单数据校验失败时的处理：重新渲染文章详情页，并把表单（含错误信息）传回。"""
        article_id = self.kwargs['article_id']
        article = get_object_or_404(Article, pk=article_id)

        return self.render_to_response({
            'form': form,
            'article': article
        })

    def form_valid(self, form):
        """表单数据验证合法后的核心逻辑：组装并保存一条评论。"""
        user = self.request.user
        # 以当前登录用户作为评论作者（取出 BlogUser 实例）
        author = BlogUser.objects.get(pk=user.pk)
        article_id = self.kwargs['article_id']
        article = get_object_or_404(Article, pk=article_id)

        # 校验：文章评论已关闭（comment_status='c'）或文章本身为关闭状态时，禁止提交
        if article.comment_status == 'c' or article.status == 'c':
            raise ValidationError("该文章评论已关闭.")

        # commit=False：先用表单数据生成 Comment 实例但暂不写库，便于补充关联字段
        comment = form.save(False)
        comment.article = article

        # 读取站点设置，判断评论是否需要审核
        from djangoblog.utils import get_blog_setting
        settings = get_blog_setting()
        if not settings.comment_need_review:
            # 不需要审核时直接置为可展示
            comment.is_enable = True
        comment.author = author

        # 若表单带了父评论 id，说明这是一条回复——关联父评论，形成楼中楼
        if form.cleaned_data['parent_comment_id']:
            parent_comment = Comment.objects.get(
                pk=form.cleaned_data['parent_comment_id'])
            comment.parent_comment = parent_comment

        # commit=True 真正写入数据库
        comment.save(True)
        # 重定向到该文章，并定位到刚发布的评论锚点（#div-comment-<id>）
        return HttpResponseRedirect(
            "%s#div-comment-%d" %
            (article.get_absolute_url(), comment.pk))


class CommentReactionView(View):
    """
    评论 Emoji 反应 API
    GET  /comment/<comment_id>/react  获取 reactions（公开访问）
    POST /comment/<comment_id>/react  切换 reaction（需要登录）
    """

    def get(self, request, comment_id):
        """获取评论的 reactions 数据（公开访问）。"""
        # 仅查询已启用（通过审核）的评论，找不到则返回 404
        comment = get_object_or_404(Comment, id=comment_id, is_enable=True)

        # 传递用户信息：已登录则用于判断是否已表态，未登录则传 None
        user = request.user if request.user.is_authenticated else None
        reactions_data = comment.get_reactions_summary(user)

        return JsonResponse({
            'success': True,
            'reactions': reactions_data
        })

    def post(self, request, comment_id):
        """切换某条评论的 Emoji 反应（已点赞则取消，未点赞则新增）。"""
        # POST 需要登录验证，未登录返回 401
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)

        # 获取评论（只有已启用的评论才能点赞）
        comment = get_object_or_404(Comment, id=comment_id, is_enable=True)

        # 获取本次提交的表情类型
        reaction_type = request.POST.get('reaction_type')

        # 校验 reaction_type 是否在系统允许的 8 种表情内，非法返回 400
        valid_reactions = [choice[0] for choice in CommentReaction.REACTION_CHOICES]
        if reaction_type not in valid_reactions:
            return JsonResponse({
                'error': 'Invalid reaction type'
            }, status=400)

        # 切换 reaction：get_or_create 查找已有记录，查不到则新建
        # （模型层 unique_together 已保证同一用户、同一评论、同一表情唯一）
        reaction, created = CommentReaction.objects.get_or_create(
            comment=comment,
            user=request.user,
            reaction_type=reaction_type
        )

        if not created:
            # 记录已存在 -> 删除它（取消点赞）
            reaction.delete()
            action = 'removed'
        else:
            # 新建成功 -> 点赞
            action = 'added'

        # 返回该评论的所有 reactions 最新统计
        reactions_data = comment.get_reactions_summary(request.user)

        return JsonResponse({
            'success': True,
            'action': action,
            'reactions': reactions_data
        })
