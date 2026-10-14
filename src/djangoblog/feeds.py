"""
djangoblog feeds.py 文件
功能：定义博客的 RSS 订阅源（Feed）
把最新发布的文章以 RSS 2.0 格式输出，供阅读器订阅
"""
from django.contrib.auth import get_user_model
from django.contrib.syndication.views import Feed
from django.utils import timezone
from django.utils.feedgenerator import Rss201rev2Feed

from blog.models import Article
from djangoblog.utils import CommonMarkdown


# 博客 RSS 订阅源类：继承 Django 的 Feed，定义订阅源的标题、链接与内容条目
class DjangoBlogFeed(Feed):
    # 使用 RSS 2.0 输出格式
    feed_type = Rss201rev2Feed

    # 订阅源的描述与标题
    description = '大巧无工,重剑无锋.'
    title = "且听风吟 大巧无工,重剑无锋. "
    link = "/feed/"

    def author_name(self):
        """返回订阅源作者昵称（取第一个用户的昵称）"""
        return get_user_model().objects.first().nickname

    def author_link(self):
        """返回订阅源作者主页链接"""
        return get_user_model().objects.first().get_absolute_url()

    def items(self):
        """返回订阅条目：最新 5 篇已发布的普通文章（type=a 且 status=p）"""
        return Article.objects.filter(type='a', status='p').order_by('-pub_time')[:5]

    def item_title(self, item):
        """返回单条订阅条目的标题"""
        return item.title

    def item_description(self, item):
        """返回单条订阅条目的正文描述（Markdown 转 HTML）"""
        return CommonMarkdown.get_markdown(item.body)

    def feed_copyright(self):
        """返回订阅源的版权信息（含当前年份）"""
        now = timezone.now()
        return "Copyright© {year} 且听风吟".format(year=now.year)

    def item_link(self, item):
        """返回单条订阅条目的跳转链接"""
        return item.get_absolute_url()

    def item_guid(self, item):
        """返回单条订阅条目的全局唯一标识（此处未实现，Django 会回退用链接作为 guid）"""
        return
