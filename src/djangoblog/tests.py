#zy: 模块精读：djangoblog 基础单元测试（TestCase）。对 utils 的 get_sha256 / CommonMarkdown / parse_dict_to_url 做冒烟测试，只断言非 None，属轻量验证。
from django.test import TestCase

from djangoblog.utils import *


class DjangoBlogTest(TestCase):
    def setUp(self):
        pass

    def test_utils(self):
        md5 = get_sha256('test')
        self.assertIsNotNone(md5)
        c = CommonMarkdown.get_markdown('''
        # Title1

        ```python
        import os
        ```

        [url](https://www.lylinux.net/)

        [ddd](http://www.baidu.com)


        ''')
        self.assertIsNotNone(c)
        d = {
            'd': 'key1',
            'd2': 'key2'
        }
        data = parse_dict_to_url(d)
        self.assertIsNotNone(data)
