# =============================================================================
# comments 应用 · 工具函数（utils.py）
# -----------------------------------------------------------------------------
# 本文件提供评论相关的辅助功能，目前只有一个：
#   send_comment_email(comment) —— 给评论作者 / 被回复者发送邮件通知。
# 逻辑：评论发表后，通知作者"感谢评论"；若该评论是回复（有 parent_comment），
#       再给被回复的原评论作者发一封"有人回复了你"的通知。
# =============================================================================
import logging

from django.utils.translation import gettext_lazy as _

from djangoblog.utils import get_current_site
from djangoblog.utils import send_email

# 模块级日志记录器，用于记录异常
logger = logging.getLogger(__name__)


def send_comment_email(comment):
    """给评论作者（以及被回复者）发送邮件通知。

    参数 comment：刚保存的 Comment 实例。
    """
    # 获取当前站点域名，用于拼出文章完整 URL
    site = get_current_site().domain
    subject = _('Thanks for your comment')
    # 文章绝对地址：https://域名 + 文章的 URL
    article_url = f"https://{site}{comment.article.get_absolute_url()}"

    # 第一封邮件：感谢评论者本人（内容为 HTML，附文章链接）
    html_content = _("""<p>Thank you very much for your comments on this site</p>
                    You can visit <a href="%(article_url)s" rel="bookmark">%(article_title)s</a>
                    to review your comments,
                    Thank you again!
                    <br />
                    If the link above cannot be opened, please copy this link to your browser.
                    %(article_url)s""") % {'article_url': article_url, 'article_title': comment.article.title}
    tomail = comment.author.email
    send_email([tomail], subject, html_content)

    # 第二封邮件：如果这条评论是回复（存在父评论），通知被回复的原评论作者
    try:
        if comment.parent_comment:
            html_content = _("""Your comment on <a href="%(article_url)s" rel="bookmark">%(article_title)s</a><br/> has 
                   received a reply. <br/> %(comment_body)s
                    <br/>   
                    go check it out!
                     <br/>
                     If the link above cannot be opened, please copy this link to your browser.
                     %(article_url)s
                    """) % {'article_url': article_url, 'article_title': comment.article.title,
                            'comment_body': comment.parent_comment.body}
            # 收件人：原评论的作者
            tomail = comment.parent_comment.author.email
            send_email([tomail], subject, html_content)
    except Exception as e:
        # 邮件发送失败不能影响主流程（评论本身已保存），只记录日志
        logger.error(e)
