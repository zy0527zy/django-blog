import logging
import time

from ipware import get_client_ip
from user_agents import parse

from blog.documents import ELASTICSEARCH_ENABLED, ElaspedTimeDocumentManager

logger = logging.getLogger(__name__)


# 页面性能统计中间件，负责记录请求耗时和客户端访问信息
class OnlineMiddleware(object):
    # 保存 Django 后续中间件或视图的调用入口
    def __init__(self, get_response=None):
        self.get_response = get_response
        super().__init__()

    # 处理每次请求，统计页面处理时间并记录性能数据
    def __call__(self, request):
        ''' page render time '''
        # 记录请求开始时间，用于计算页面处理耗时。
        start_time = time.time()
        # 调用下游中间件及视图，获取 Django 生成的响应。
        response = self.get_response(request)
        # 读取客户端浏览器标识，并在后续提取 IP 和设备信息。
        http_user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip, _ = get_client_ip(request)
        user_agent = parse(http_user_agent)
        # 仅对非流式响应计算耗时、记录性能日志并替换页面占位符。
        if not response.streaming:
            try:
                # 计算请求耗时，单位为秒。
                cast_time = time.time() - start_time
                # 项目配置启用 Elasticsearch 时，尝试保存本次请求的性能日志。
                if ELASTICSEARCH_ENABLED:
                    time_taken = round((cast_time) * 1000, 2)
                    url = request.path
                    from django.utils import timezone
                    # 将访问路径、耗时、访问时间、设备和 IP 信息写入性能索引。
                    ElaspedTimeDocumentManager.create(
                        url=url,
                        time_taken=time_taken,
                        log_datetime=timezone.now(),
                        useragent=user_agent,
                        ip=ip)
                # 替换响应内容中的耗时占位符，供页面显示加载时间。
                response.content = response.content.replace(
                    b'<!!LOAD_TIMES!!>', str.encode(str(cast_time)[:5]))
            # 记录统计过程中的异常，避免统计失败影响正常响应。
            except Exception as e:
                logger.error("Error OnlineMiddleware: %s" % e)

        # 将处理完成的响应返回给 Django。
        return response
