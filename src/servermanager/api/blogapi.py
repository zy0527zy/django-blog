#zly: 模块说明：博客相关数据查询接口封装，提供文章搜索、分类查询、最新文章获取能力。
"""
servermanager/api/blogapi.py 文件
功能：博客相关数据查询接口封装类，提供文章搜索、分类查询、最新文章获取能力
对接Haystack搜索引擎与博客模型，供微信机器人调用获取博客数据
"""
from haystack.query import SearchQuerySet

from blog.models import Article, Category


#zly: BlogApi：封装博客查询方法，供微信机器人统一调用。
class BlogApi:
    """博客业务查询API类，封装文章、分类相关查询方法，对外提供统一数据查询入口"""

    #zly: 初始化 Haystack 查询对象，并设定单次最多返回 8 条，避免微信图文消息过长。
    def __init__(self):
        """构造方法：初始化搜索引擎查询对象，设置单次查询最大返回条数为8条"""
        self.searchqueryset = SearchQuerySet()
        self.searchqueryset.auto_query('')
        self.__max_takecount__ = 8

    #zly: 按关键词检索文章，load_all() 一次性取出模型对象。
    def search_articles(self, query):
        """
        根据关键词使用Haystack搜索引擎检索文章
        :param query: 搜索关键词
        :return: 最多8条搜索结果
        """
        sqs = self.searchqueryset.auto_query(query)
        sqs = sqs.load_all()
        return sqs[:self.__max_takecount__]

    #zly: 查询博客全部文章分类列表。
    def get_category_lists(self):
        """查询博客全部文章分类列表"""
        return Category.objects.all()

    #zly: 按分类名称查询该分类下的文章。
    def get_category_articles(self, categoryname):
        """
        根据分类名称查询该分类下文章
        :param categoryname: 分类名称
        :return: 最多8条对应分类文章，无数据返回None
        """
        articles = Article.objects.filter(category__name=categoryname)
        if articles:
            return articles[:self.__max_takecount__]
        return None

    #zly: 获取最新文章列表，最多返回 8 条。
    def get_recent_articles(self):
        """获取最新文章列表，最多返回8条"""
        return Article.objects.all()[:self.__max_takecount__]
