#hzh: 本模块提供Elasticsearch搜索索引的构建管理命令。
from django.core.management.base import BaseCommand

from blog.documents import ElapsedTimeDocument, ArticleDocumentManager, ElaspedTimeDocumentManager, \
    ELASTICSEARCH_ENABLED


# TODO 参数化
#hzh: 命令包含索引删除和重建操作，执行前应确认目标环境。
class Command(BaseCommand):
    help = 'build search index'

    #hzh: 启用Elasticsearch时构建耗时索引并重建文章索引。
    def handle(self, *args, **options):
        if ELASTICSEARCH_ENABLED:
            ElaspedTimeDocumentManager.build_index()
            manager = ElapsedTimeDocument()
            manager.init()
            manager = ArticleDocumentManager()
            manager.delete_index()
            manager.rebuild()
