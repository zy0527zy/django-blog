"""
servermanager MemcacheStorage.py 文件
功能：自定义微信机器人会话存储类，继承Werobot的SessionStorage，使用Django缓存(Memcache)存储微信会话数据
提供会话读取、写入、删除、可用性检测方法，为robot机器人提供会话能力
"""
from werobot.session import SessionStorage
from werobot.utils import json_loads, json_dumps
from djangoblog.utils import cache


"""基于Memcache实现的Werobot会话存储类，接管微信机器人用户会话读写"""
class MemcacheStorage(SessionStorage):
    """
    构造方法：初始化缓存key前缀，用于区分不同业务的缓存key
    :param prefix: 缓存键名前缀，默认ws_
    """
    def __init__(self, prefix='ws_'):
        self.prefix = prefix
        self.cache = cache

    """属性方法：检测Memcache缓存服务是否可用，通过写入并读取测试键判断"""
    @property
    def is_available(self):
        value = "1"
        self.set('checkavaliable', value=value)
        return value == self.get('checkavaliable')

    """拼接完整缓存key，增加前缀防止key冲突"""
    def key_name(self, s):
        return '{prefix}{s}'.format(prefix=self.prefix, s=s)

    """根据会话id读取会话数据，json字符串反序列化为python对象"""
    def get(self, id):
        id = self.key_name(id)
        session_json = self.cache.get(id) or '{}'
        return json_loads(session_json)

    """写入会话数据，将python对象序列化为json字符串存入缓存"""
    def set(self, id, value):
        id = self.key_name(id)
        self.cache.set(id, json_dumps(value))

    """根据会话id删除缓存中的会话记录"""
    def delete(self, id):
        id = self.key_name(id)
        self.cache.delete(id)
