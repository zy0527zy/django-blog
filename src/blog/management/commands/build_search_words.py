#hzh: 本模块从分类和标签数据中提取搜索词候选集合。
from django.core.management.base import BaseCommand

from blog.models import Tag, Category


# TODO 参数化
class Command(BaseCommand):
    help = 'build search words'

    #hzh: 用集合去重分类名和标签名，最后逐行输出搜索词。
    def handle(self, *args, **options):
        datas = set([t.name for t in Tag.objects.all()] +
                    [t.name for t in Category.objects.all()])
        print('\n'.join(datas))
