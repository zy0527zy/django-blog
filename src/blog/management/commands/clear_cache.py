#hzh: 本模块提供清空项目缓存的Django管理命令。
from django.core.management.base import BaseCommand

from djangoblog.utils import cache


class Command(BaseCommand):
    help = 'clear the whole cache'

    #hzh: cache.clear会清理当前缓存后端中的全部缓存项，而非仅清除某篇文章。
    def handle(self, *args, **options):
        cache.clear()
        self.stdout.write(self.style.SUCCESS('Cleared cache\n'))
