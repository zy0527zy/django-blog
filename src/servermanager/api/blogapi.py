"""
servermanager/api/blogapi.py 文件
功能：博客相关数据查询接口封装类，提供文章搜索、分类查询、最新文章获取能力
对接Haystack搜索引擎与博客模型，供微信机器人调用获取博客数据
"""
from haystack.query import SearchQuerySet
from blog.models import Article, Category


"""博客业务查询API类，封装文章、分类相关查询方法，对外提供统一数据查询入口"""
class BlogApi:
    """
    构造方法：初始化搜索引擎查询对象，设置单次查询最大返回条数为8条
    """
    def __init__(self):
        self.searchqueryset = SearchQuerySet()
        self.searchqueryset.auto_query('')
        self.__max_takecount__ = 8

    """
    根据关键词使用Haystack搜索引擎检索文章
    :param query: 搜索关键词
    :return: 最多8条搜索结果
    """
    def search_articles(self, query):
        sqs = self.searchqueryset.auto_query(query)
        sqs = sqs.load_all()
        return sqs[:self.__max_takecount__]

    """查询博客全部文章分类列表"""
    def get_category_lists(self):
        return Category.objects.all()

    """
    根据分类名称查询该分类下文章
    :param categoryname: 分类名称
    :return: 最多8条对应分类文章，无数据返回None
    """
    def get_category_articles(self, categoryname):
        articles = Article.objects.filter(category__name=categoryname)
        if articles:
            return articles[:self.__max_takecount__]
        return None

    """获取最新文章列表，最多返回8条"""
    def get_recent_articles(self):
        return Article.objects.all()[:self.__max_takecount__]
