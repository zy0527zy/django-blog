import time

import elasticsearch.client
from django.conf import settings
from elasticsearch_dsl import Document, InnerDoc, Date, Integer, Long, Text, Object, GeoPoint, Keyword, Boolean
from elasticsearch_dsl.connections import connections

from blog.models import Article

ELASTICSEARCH_ENABLED = hasattr(settings, 'ELASTICSEARCH_DSL')

if ELASTICSEARCH_ENABLED:
    from elasticsearch import Elasticsearch

    es_config = settings.ELASTICSEARCH_DSL['default']

    # 处理 hosts 配置，确保有 scheme
    hosts = es_config['hosts']
    if isinstance(hosts, str):
        # 如果没有 scheme，自动添加 http://
        if not hosts.startswith(('http://', 'https://')):
            hosts = f'http://{hosts}'
        hosts = [hosts]
    elif isinstance(hosts, list):
        # 处理列表中的每个 host
        processed_hosts = []
        for host in hosts:
            if not host.startswith(('http://', 'https://')):
                host = f'http://{host}'
            processed_hosts.append(host)
        hosts = processed_hosts

    # ES 连接配置（动态适配认证方式）
    es_params = {
        'hosts': hosts,
        'verify_certs': es_config.get('verify_certs', False),
    }

    # 支持用户名密码认证（ES 8.x 默认启用安全特性）
    if 'username' in es_config and 'password' in es_config:
        es_params['basic_auth'] = (es_config['username'], es_config['password'])

    # 支持 API Key 认证
    if 'api_key' in es_config:
        es_params['api_key'] = es_config['api_key']

    # 支持证书认证
    if 'ca_certs' in es_config:
        es_params['ca_certs'] = es_config['ca_certs']

    # 支持客户端证书
    if 'client_cert' in es_config and 'client_key' in es_config:
        es_params['client_cert'] = es_config['client_cert']
        es_params['client_key'] = es_config['client_key']

    # 创建连接
    es = Elasticsearch(**es_params)
    connections.create_connection(**es_params)

    # 设置 GeoIP pipeline
    try:
        es.ingest.get_pipeline(id='geoip')
    except elasticsearch.exceptions.NotFoundError:
        es.ingest.put_pipeline(id='geoip', body={
            "description": "Add geoip info",
            "processors": [
                {
                    "geoip": {
                        "field": "ip"
                    }
                }
            ]
        })


# Elasticsearch 中保存访问者 IP 地理位置信息的内嵌文档
class GeoIp(InnerDoc):
    continent_name = Keyword()
    country_iso_code = Keyword()
    country_name = Keyword()
    location = GeoPoint()


# 保存客户端浏览器名称和版本信息
class UserAgentBrowser(InnerDoc):
    Family = Keyword()
    Version = Keyword()


# 保存客户端操作系统名称和版本信息
class UserAgentOS(UserAgentBrowser):
    pass


# 保存客户端设备品牌和型号等信息
class UserAgentDevice(InnerDoc):
    Family = Keyword()
    Brand = Keyword()
    Model = Keyword()


# 汇总浏览器、操作系统和设备等客户端信息
class UserAgent(InnerDoc):
    browser = Object(UserAgentBrowser, required=False)
    os = Object(UserAgentOS, required=False)
    device = Object(UserAgentDevice, required=False)
    string = Text()
    is_bot = Boolean()


# 页面性能日志文档，保存 URL、耗时、IP 和客户端信息
class ElapsedTimeDocument(Document):
    url = Keyword()
    time_taken = Long()
    log_datetime = Date()
    ip = Keyword()
    geoip = Object(GeoIp, required=False)
    useragent = Object(UserAgent, required=False)

    class Index:
        name = 'performance'
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }


# 页面性能日志管理器，负责性能索引的创建、删除和写入
class ElaspedTimeDocumentManager:
    @staticmethod
    # 检查 performance 性能索引，不存在时才初始化创建。
    def build_index():
        from elasticsearch import Elasticsearch
        # 使用已配置好的连接参数
        client = Elasticsearch(**es_params)
        # 先查询索引是否存在，避免重复初始化。
        res = client.indices.exists(index="performance")
        if not res:
            ElapsedTimeDocument.init()

    @staticmethod
    def delete_index():
        from elasticsearch import Elasticsearch
        es = Elasticsearch(**es_params)
        try:
            # 删除性能索引；如果不存在，则由下方异常处理忽略。
            es.indices.delete(index='performance')
        except elasticsearch.exceptions.NotFoundError:
            pass

    @staticmethod
    # 整理访问设备信息，并向 performance 索引写入性能日志。
    def create(url, time_taken, log_datetime, useragent, ip):
        # 写入前确保性能索引已经存在。
        ElaspedTimeDocumentManager.build_index()
        # 将浏览器、操作系统、设备等信息整理为嵌套文档。
        ua = UserAgent()
        ua.browser = UserAgentBrowser()
        ua.browser.Family = useragent.browser.family
        ua.browser.Version = useragent.browser.version_string

        ua.os = UserAgentOS()
        ua.os.Family = useragent.os.family
        ua.os.Version = useragent.os.version_string

        ua.device = UserAgentDevice()
        ua.device.Family = useragent.device.family
        ua.device.Brand = useragent.device.brand
        ua.device.Model = useragent.device.model
        ua.string = useragent.ua_string
        ua.is_bot = useragent.is_bot

        # 构造性能日志，使用当前毫秒时间戳作为文档 ID。
        doc = ElapsedTimeDocument(
            meta={
                'id': int(
                    round(
                        time.time() *
                        1000))
            },
            url=url,
            time_taken=time_taken,
            log_datetime=log_datetime,
            useragent=ua, ip=ip)
        # 保存日志，并通过 geoip 管道尝试补充 IP 地理信息。
        doc.save(pipeline="geoip")


# Elasticsearch 文章文档结构，用于保存可全文检索的文章信息
class ArticleDocument(Document):
    body = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    title = Text(analyzer='ik_max_word', search_analyzer='ik_smart')
    author = Object(properties={
        'nickname': Text(analyzer='ik_max_word', search_analyzer='ik_smart'),
        'id': Integer()
    })
    category = Object(properties={
        'name': Text(analyzer='ik_max_word', search_analyzer='ik_smart'),
        'id': Integer()
    })
    tags = Object(properties={
        'name': Text(analyzer='ik_max_word', search_analyzer='ik_smart'),
        'id': Integer()
    })

    pub_time = Date()
    status = Text()
    comment_status = Text()
    type = Text()
    views = Integer()
    article_order = Integer()

    class Index:
        name = 'blog'
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }


# 文章搜索文档管理器，负责文章索引的创建、转换、重建和更新
class ArticleDocumentManager():

    # 创建文章索引管理器时，初始化 blog 搜索索引。
    def __init__(self):
        self.create_index()

    # 根据 ArticleDocument 的字段映射初始化文章搜索索引。
    def create_index(self):
        ArticleDocument.init()

    def delete_index(self):
        from elasticsearch import Elasticsearch
        es = Elasticsearch(**es_params)
        try:
            # 删除 blog 搜索索引；不存在时忽略对应异常。
            es.indices.delete(index='blog')
        except elasticsearch.exceptions.NotFoundError:
            pass

    # 将 Django 的 Article 对象转换为 Elasticsearch 文档
    def convert_to_doc(self, articles):
        return [
            ArticleDocument(
                meta={
                    'id': article.id},
                body=article.body,
                title=article.title,
                author={
                    'nickname': article.author.username,
                    'id': article.author.id},
                category={
                    'name': article.category.name,
                    'id': article.category.id},
                tags=[
                    {
                        'name': t.name,
                        'id': t.id} for t in article.tags.all()],
                pub_time=article.pub_time,
                status=article.status,
                comment_status=article.comment_status,
                type=article.type,
                views=article.views,
                article_order=article.article_order) for article in articles]

    # 根据文章数据重新建立 Elasticsearch 搜索索引
    def rebuild(self, articles=None):
        ArticleDocument.init()
        # 未提供文章集合或传入空集合时，默认获取数据库中的全部文章。
        articles = articles if articles else Article.objects.all()
        docs = self.convert_to_doc(articles)
        for doc in docs:
            doc.save()

    # 将传入的文章搜索文档逐个保存到 Elasticsearch。
    def update_docs(self, docs):
        for doc in docs:
            doc.save()
