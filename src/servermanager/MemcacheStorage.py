#zly: 模块说明：自定义微信机器人会话存储类，继承 WeRoBot 的 SessionStorage，使用 Django 缓存保存会话数据。
# pylint: disable=broad-exception-caught
# 说明：缓存后端异常类型因部署环境而异，此处统一兜底降级，避免会话存储故障拖垮机器人。
"""
servermanager MemcacheStorage.py 文件
功能：自定义微信机器人会话存储类，继承Werobot的SessionStorage，使用Django缓存(Memcache)存储微信会话数据
提供会话读取、写入、删除、可用性检测方法，为robot机器人提供会话能力
"""
import logging

from werobot.session import SessionStorage
from werobot.utils import json_dumps, json_loads

from djangoblog.utils import cache

#zly: 模块日志实例。
logger = logging.getLogger(__name__)


#zly: MemcacheStorage：基于 Django 缓存实现的 WeRoBot 会话存储，接管微信机器人用户会话读写。
class MemcacheStorage(SessionStorage):
    """基于Memcache实现的Werobot会话存储类，接管微信机器人用户会话读写"""

    #zly: 构造方法：初始化缓存 key 前缀，复用 djangoblog.utils 中的 Django cache 对象。
    def __init__(self, prefix='ws_'):
        """
        构造方法：初始化缓存key前缀，用于区分不同业务的缓存key
        :param prefix: 缓存键名前缀，默认ws_
        """
        self.prefix = prefix
        self.cache = cache

    #zly: 属性方法：检测缓存服务是否可用，通过写入并读取测试键判断；异常时视为不可用。
    @property
    def is_available(self):
        """检测Memcache缓存服务是否可用，通过写入并读取测试键判断；异常时返回 False。"""
        try:
            value = "1"
            self.set('checkavaliable', value=value)
            return value == self.get('checkavaliable')
        except Exception:
            logger.warning('Memcache 可用性检测失败，降级为文件会话存储', exc_info=True)
            return False

    #zly: 拼接完整缓存 key，增加前缀防止 key 冲突。
    def key_name(self, s):
        """拼接完整缓存key，增加前缀防止key冲突"""
        return f'{self.prefix}{s}'

    #zly: 根据会话 id 读取会话数据，json 字符串反序列化为 Python 对象。
    def get(self, id):
        """根据会话id读取会话数据，json字符串反序列化为python对象"""
        try:
            session_json = self.cache.get(self.key_name(id)) or '{}'
            return json_loads(session_json)
        except Exception:
            logger.warning('读取会话缓存失败: %s', id, exc_info=True)
            return {}

    #zly: 写入会话数据，将 Python 对象序列化为 json 字符串存入缓存。
    def set(self, id, value):
        """写入会话数据，将python对象序列化为json字符串存入缓存"""
        try:
            self.cache.set(self.key_name(id), json_dumps(value))
        except Exception:
            logger.warning('写入会话缓存失败: %s', id, exc_info=True)

    #zly: 根据会话 id 删除缓存中的会话记录。
    def delete(self, id):
        """根据会话id删除缓存中的会话记录"""
        try:
            self.cache.delete(self.key_name(id))
        except Exception:
            logger.warning('删除会话缓存失败: %s', id, exc_info=True)
