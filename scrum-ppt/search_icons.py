# -*- coding: utf-8 -*-
import subprocess, sys

tool = r'C:\Users\刘雨婷\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.skills\ppt\scripts\iconpark_tool.py'
queries = ['目标', '团队', '代码', '清单 任务', '时钟 提醒', '会议 讨论', '眼睛 查看', '刷新 循环', '指南针 引导', '奖杯 交付', '警告 风险', '问题 疑问']
for q in queries:
    print('=' * 20, q, '=' * 20)
    r = subprocess.run([sys.executable, tool, 'search', '--query', q, '--limit', '5'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(r.stdout[:1200])
    if r.stderr.strip():
        print('STDERR:', r.stderr[:300])
