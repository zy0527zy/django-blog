"""
djangoblog spider_notify.py 文件
功能：搜索引擎主动推送（ping）
把新发布的文章 URL 主动推送给百度等搜索引擎，加快内容收录
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


#zy: 模块精读：向百度等搜索引擎主动推送新文章 URL，加快收录。notify() 是对 baidu_notify() 的薄封装。
# 搜索引擎通知工具类：封装主动推送接口
class SpiderNotify():
    @staticmethod
    def baidu_notify(urls):
        """向百度主动推送 URL：把多个 URL 用换行拼接后 POST 到百度推送接口"""
        try:
            data = '\n'.join(urls)
            result = requests.post(settings.BAIDU_NOTIFY_URL, data=data)
            logger.info(result.text)
        except Exception as e:
            logger.error(e)

    @staticmethod
    def notify(url):
        """通知入口：默认调用百度推送"""
        #zy: 【质量】这里把单个 url 直接传给 baidu_notify(urls)，而 baidu_notify 内 '\n'.join(urls) 会把字符串逐字符用换行拆开，
        #zy: 实际应传 [url]（列表）；调用方若传单个字符串会导致推送给百度的数据错乱。
        SpiderNotify.baidu_notify(url)
