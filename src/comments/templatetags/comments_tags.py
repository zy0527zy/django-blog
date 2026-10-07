# =============================================================================
# comments 应用 · 自定义模板标签（templatetags/comments_tags.py）
# -----------------------------------------------------------------------------
# 本文件定义评论模块在 Django 模板中使用的自定义标签，供 HTML 模板调用：
#   1. parse_commenttree：递归取出一条评论的所有子评论（楼中楼回复列表）
#   2. show_comment_item：渲染单条评论的片段模板（带层级缩进）
# 模板中先 {% load comments_tags %} 才能使用这些标签。
# =============================================================================
from django import template

# 模板标签库实例：注册自定义标签必须用它
register = template.Library()


@register.simple_tag
def parse_commenttree(commentlist, comment):
    """获得当前评论子评论的列表
        用法: {% parse_commenttree article_comments comment as childcomments %}
    实现"楼中楼"的关键：从某条评论出发，递归查找它的所有子评论（含孙评论），
    返回一个展平的列表，供模板循环渲染嵌套回复。
    """
    datas = []

    def parse(c):
        # 找出 c 的直接子评论（parent_comment=c 且已启用展示）
        childs = commentlist.filter(parent_comment=c, is_enable=True)
        for child in childs:
            datas.append(child)
            # 递归：继续找 child 的子评论，直到没有更深层
            parse(child)

    parse(comment)
    return datas


@register.inclusion_tag('comments/tags/comment_item.html')
def show_comment_item(comment, ischild):
    """评论"""
    # 渲染单条评论片段：ischild 表示是否为子评论（决定缩进层级）
    depth = 1 if ischild else 2
    return {
        'comment_item': comment,
        'depth': depth
    }
