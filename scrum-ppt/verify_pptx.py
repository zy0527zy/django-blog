# -*- coding: utf-8 -*-
import zipfile, re, shutil, os

src = r'D:\DjangoBlog\scrum-ppt\export\Scrum敏捷开发方法.pptx'
dst_dir = r'C:\Users\刘雨婷\Desktop\实习'
dst = os.path.join(dst_dir, 'Scrum敏捷开发方法.pptx')

# 校验 pptx 是合法 zip 且含 10 张幻灯片
with zipfile.ZipFile(src) as z:
    slides = [n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$', n)]
    print('valid pptx, slide count =', len(slides))

shutil.copy2(src, dst)
print('copied to:', dst, os.path.getsize(dst), 'bytes')
