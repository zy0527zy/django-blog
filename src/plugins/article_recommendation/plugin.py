"""
文章推荐插件主文件
功能：根据文章标签、分类进行相关文章推荐，推荐不足时回退热门文章；
支持文章底部、侧边栏多位置渲染，提供前端CSS与JS资源。
"""
import logging
from djangoblog.plugin_manage.base_plugin import BasePlugin
from djangoblog.plugin_manage import hooks
from djangoblog.plugin_manage.hook_constants import ARTICLE_DETAIL_LOAD
from blog.models import Article

logger = logging.getLogger(__name__)


class ArticleRecommendationPlugin(BasePlugin):
    """文章推荐插件类，继承基础插件，实现多位置文章推荐展示逻辑"""
    PLUGIN_NAME = '文章推荐'
    PLUGIN_DESCRIPTION = '智能文章推荐系统，支持多位置展示'
    PLUGIN_VERSION = '1.0.0'
    PLUGIN_AUTHOR = 'liangliangyy'
    
    # 支持的位置
    SUPPORTED_POSITIONS = ['article_bottom']
    
    # 各位置优先级
    POSITION_PRIORITIES = {
        'article_bottom': 80,  # 文章底部优先级
    }
    
    # 插件配置
    CONFIG = {
        'article_bottom_count': 8,  # 文章底部推荐数量
        'sidebar_count': 5,         # 侧边栏推荐数量
        'enable_category_fallback': True,  # 启用分类回退
        'enable_popular_fallback': True,   # 启用热门文章回退
    }
    
    def register_hooks(self):
        """注册钩子：绑定文章详情加载事件"""
        hooks.register(ARTICLE_DETAIL_LOAD, self.on_article_detail_load)
    
    def on_article_detail_load(self, article, context, request, *args, **kwargs):
        """
        文章详情页加载钩子回调
        :param article: 当前浏览文章对象
        :param context: 页面上下文
        :param request: http请求对象
        """
        # 可以在这里预加载推荐数据到context中
        recommendations = self.get_recommendations(article)
        context['article_recommendations'] = recommendations
    
    def should_display(self, position, context, **kwargs):
        """
        控制插件在指定位置是否渲染
        :param position: 渲染位置标识
        :param context: 页面上下文
        :return: bool，True展示，False隐藏
        """
        # 只在文章详情页底部显示
        if position == 'article_bottom':
            article = kwargs.get('article') or context.get('article')
            # 检查是否有文章对象，以及是否不是索引页面
            is_index = context.get('isindex', False) if hasattr(context, 'get') else False
            return article is not None and not is_index
            
        return False
    
    def render_article_bottom_widget(self, context, **kwargs):
        """
        渲染文章底部推荐组件
        :param context: 页面上下文
        :return: 渲染后的html内容，无推荐返回None
        """
        article = kwargs.get('article') or context.get('article')
        if not article:
            return None
        
        # 使用配置的数量，也可以通过kwargs覆盖
        count = kwargs.get('count', self.CONFIG['article_bottom_count'])
        recommendations = self.get_recommendations(article, count=count)
        if not recommendations:
            return None
        
        # 将RequestContext转换为普通字典
        context_dict = {}
        if hasattr(context, 'flatten'):
            context_dict = context.flatten()
        elif hasattr(context, 'dicts'):
            # 合并所有上下文字典
            for d in context.dicts:
                context_dict.update(d)
        
        template_context = {
            'recommendations': recommendations,
            'article': article,
            'title': '相关推荐',
            **context_dict
        }
            
        return self.render_template('bottom_widget.html', template_context)
    
    def render_sidebar_widget(self, context, **kwargs):
        """
        渲染侧边栏推荐组件
        :param context: 页面上下文
        :return: 渲染后的html内容，无推荐返回None
        """
        article = context.get('article')
        
        # 使用配置的数量，也可以通过kwargs覆盖
        count = kwargs.get('count', self.CONFIG['sidebar_count'])
        
        if article:
            # 文章页面，显示相关文章
            recommendations = self.get_recommendations(article, count=count)
            title = '相关文章'
        else:
            # 其他页面，显示热门文章
            recommendations = self.get_popular_articles(count=count)
            title = '热门推荐'
            
        if not recommendations:
            return None
        
        # 将RequestContext转换为普通字典
        context_dict = {}
        if hasattr(context, 'flatten'):
            context_dict = context.flatten()
        elif hasattr(context, 'dicts'):
            # 合并所有上下文字典
            for d in context.dicts:
                context_dict.update(d)
        
        template_context = {
            'recommendations': recommendations,
            'title': title,
            **context_dict
        }
            
        return self.render_template('sidebar_widget.html', template_context)
    
    def get_css_files(self):
        """返回插件需要加载的css文件列表"""
        return ['css/recommendation.css']
    
    def get_js_files(self):
        """返回JS文件"""
        return ['js/recommendation.js']
    
    def get_recommendations(self, article, count=5):
        """
        获取相关推荐文章，策略：标签优先→分类兜底→热门兜底
        :param article: 当前文章对象
        :param count: 需要获取的推荐条数
        :return: 推荐文章列表
        """
        if not article:
            return []
        
        recommendations = []
        
        # 1. 基于标签的推荐
        if article.tags.exists():
            tag_ids = list(article.tags.values_list('id', flat=True))
            tag_based = list(Article.objects.filter(
                status='p',
                tags__id__in=tag_ids
            ).exclude(
                id=article.id
            ).exclude(
                title__isnull=True
            ).exclude(
                title__exact=''
            ).distinct().order_by('-views')[:count])
            recommendations.extend(tag_based)
        
        # 2. 如果数量不够，基于分类推荐
        if len(recommendations) < count and self.CONFIG['enable_category_fallback']:
            needed = count - len(recommendations)
            existing_ids = [r.id for r in recommendations] + [article.id]
            
            category_based = list(Article.objects.filter(
                status='p',
                category=article.category
            ).exclude(
                id__in=existing_ids
            ).exclude(
                title__isnull=True
            ).exclude(
                title__exact=''
            ).order_by('-views')[:needed])
            recommendations.extend(category_based)
        
        # 3. 如果还是不够，推荐热门文章
        if len(recommendations) < count and self.CONFIG['enable_popular_fallback']:
            needed = count - len(recommendations)
            existing_ids = [r.id for r in recommendations] + [article.id]
            
            popular_articles = list(Article.objects.filter(
                status='p'
            ).exclude(
                id__in=existing_ids
            ).exclude(
                title__isnull=True
            ).exclude(
                title__exact=''
            ).order_by('-views')[:needed])
            recommendations.extend(popular_articles)
        
        # 过滤掉无效的推荐
        valid_recommendations = []
        for rec in recommendations:
            if rec.title and len(rec.title.strip()) > 0:
                valid_recommendations.append(rec)
            else:
                logger.warning(f"过滤掉空标题文章: ID={rec.id}, 标题='{rec.title}'")
        
        # 调试：记录推荐结果
        logger.info(f"原始推荐数量: {len(recommendations)}, 有效推荐数量: {len(valid_recommendations)}")
        for i, rec in enumerate(valid_recommendations):
            logger.info(f"推荐 {i+1}: ID={rec.id}, 标题='{rec.title}', 长度={len(rec.title)}")
        
        return valid_recommendations[:count]
    
    def get_popular_articles(self, count=3):
        """
        获取全站热门文章，按浏览量降序
        :param count: 获取条数
        :return: 热门文章列表
        """
        return list(Article.objects.filter(
            status='p'
        ).order_by('-views')[:count])


# 实例化插件
plugin = ArticleRecommendationPlugin()
