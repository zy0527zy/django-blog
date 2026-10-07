# =============================================================================
# comments 应用 · 数据模型（MVT 中的 M 层）
# -----------------------------------------------------------------------------
# 本文件定义两个模型类，由 Django ORM 映射为数据库中的两张表：
#   1. Comment          -> comments_comment            文章评论（支持"楼中楼"回复）
#   2. CommentReaction  -> comments_commentreaction    评论的 Emoji 反应 / 点赞
# Comment 通过三个外键分别关联：所属文章(Article)、评论作者(BlogUser)、父评论(自身)，
# 是"表与表之间关联"的典型例子。
# =============================================================================
from django.conf import settings
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from blog.models import Article


# Create your models here.

class Comment(models.Model):
    """文章评论模型，对应数据库表 comments_comment。

    一条评论必须属于一篇文章、有一个作者；若为"回复某条评论"，
    则通过 parent_comment 指向被回复的评论（自关联），从而形成楼中楼结构。
    """

    # 评论正文，限制 300 字
    body = models.TextField('正文', max_length=300)
    # 创建时间：默认取当前时间（now 为可调用对象，每次创建实例时求值）
    creation_time = models.DateTimeField(_('creation time'), default=now)
    # 最后修改时间：同样默认当前时间
    last_modify_time = models.DateTimeField(_('last modify time'), default=now)

    # 外键 1：评论作者，关联项目自定义用户模型（settings.AUTH_USER_MODEL）
    # on_delete=CASCADE 表示用户被删除时，其评论一并删除
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('author'),
        on_delete=models.CASCADE)

    # 外键 2：所属文章，关联 blog.Article；文章删除时其评论级联删除
    article = models.ForeignKey(
        Article,
        verbose_name=_('article'),
        on_delete=models.CASCADE)

    # 外键 3：父评论，关联"自身"（'self'），实现楼中楼回复
    # blank=True/null=True 允许为空——空表示这是一条顶层评论，而非回复
    parent_comment = models.ForeignKey(
        'self',
        verbose_name=_('parent comment'),
        blank=True,
        null=True,
        on_delete=models.CASCADE)

    # 是否启用（是否通过审核、对外展示）：默认 False，需审核后才置为 True
    is_enable = models.BooleanField(_('enable'),
                                    default=False, blank=False, null=False)

    class Meta:
        # 默认按 id 倒序，即新评论排在前面
        ordering = ['-id']
        # 后台管理中显示的名称
        verbose_name = _('comment')
        verbose_name_plural = verbose_name
        # latest() / earliest() 默认依据的字段
        get_latest_by = 'id'
        indexes = [
            # 优化评论列表查询：article + parent_comment + is_enable 组合索引
            models.Index(fields=['article', 'parent_comment', 'is_enable'], name='idx_art_parent_enable'),
            # 优化侧边栏评论查询：is_enable + id 组合索引
            models.Index(fields=['is_enable', '-id'], name='idx_enable_id'),
        ]

    def __str__(self):
        # 直接显示正文，便于后台和调试阅读
        return self.body

    def get_reactions_summary(self, user=None):
        """
        获取评论的 reactions 统计信息
        返回格式: {
            '👍': {
                'count': 5,
                'has_reacted': True,
                'users': ['Alice', 'Bob', 'Charlie']
            },
            '❤️': {'count': 3, 'has_reacted': False, 'users': [...]},
            ...
        }
        """
        from django.db.models import Count

        # 按表情类型分组，统计该评论每种 Emoji 的数量
        reactions = CommentReaction.objects.filter(
            comment=self
        ).values('reaction_type').annotate(count=Count('id'))

        result = {}
        for reaction in reactions:
            emoji = reaction['reaction_type']

            # 获取该 emoji 的所有点赞用户（select_related 一次性取出用户，避免 N+1 查询）
            reaction_users = CommentReaction.objects.filter(
                comment=self,
                reaction_type=emoji
            ).select_related('user')[:10]  # 最多显示 10 个用户

            # 优先显示昵称，没有昵称则用用户名
            user_names = [r.user.nickname or r.user.username for r in reaction_users]

            result[emoji] = {
                'count': reaction['count'],
                'has_reacted': False,
                'users': user_names
            }

            # 若传入已登录用户，标记该用户是否已对此表情表态
            if user and user.is_authenticated:
                result[emoji]['has_reacted'] = CommentReaction.objects.filter(
                    comment=self,
                    user=user,
                    reaction_type=emoji
                ).exists()

        return result


class CommentReaction(models.Model):
    """
    评论的 Emoji 反应 / 点赞模型，对应表 comments_commentreaction。

    记录"哪个用户对哪条评论点了哪种表情"。
    """

    # 系统支持的 8 种 Emoji：第一项为实际存入的表情，第二项为英文标识
    REACTION_CHOICES = [
        ('👍', 'thumbs_up'),
        ('👎', 'thumbs_down'),
        ('❤️', 'heart'),
        ('😄', 'laugh'),
        ('🎉', 'hooray'),
        ('😕', 'confused'),
        ('🚀', 'rocket'),
        ('👀', 'eyes'),
    ]

    # 外键：所属评论；related_name='reactions' 可通过 comment.reactions 反查所有反应
    comment = models.ForeignKey(
        Comment,
        verbose_name=_('comment'),
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    # 外键：表态的用户
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('user'),
        on_delete=models.CASCADE
    )
    # 表情类型，取值限定在 REACTION_CHOICES 内
    reaction_type = models.CharField(
        _('reaction type'),
        max_length=10,
        choices=REACTION_CHOICES
    )
    # 创建时间：auto_now_add 在第一次插入时自动写入，之后不变
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('comment reaction')
        verbose_name_plural = _('comment reactions')
        # 联合唯一：每个用户对同一评论的同一种 emoji 只能点一次（防止重复点赞）
        unique_together = ['comment', 'user', 'reaction_type']
        indexes = [
            # 优化"按评论 + 表情类型"的统计查询
            models.Index(fields=['comment', 'reaction_type'], name='idx_comment_reaction'),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.reaction_type} on comment {self.comment.id}'
