#hzh: 本模块定义文章全文搜索索引的数据字段及收录条件。
from haystack import indexes

from blog.models import Article


# Haystack 文章搜索索引，定义 Article 中需要进入全文搜索的数据
#hzh: 索引绑定Article模型，index_queryset仅选择已发布的文章。
class ArticleIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title', stored=True)
    body = indexes.CharField(model_attr='body', stored=True)

    # 指定当前搜索索引对应 Article 模型
    def get_model(self):
        return Article

    # 只将已发布文章加入搜索索引，草稿不会被搜索到
    def index_queryset(self, using=None):
        return self.get_model().objects.filter(status='p')
