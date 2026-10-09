# -*- coding: utf-8 -*-
import pymupdf

pdf_path = r'C:\Users\刘雨婷\Desktop\实习\作业.pdf'
doc = pymupdf.open(pdf_path)
page = doc[2]
print('page rect:', page.rect)
# 图3.11区域（PDF点坐标，依据2x渲染图980x1483换算）
clip = pymupdf.Rect(78, 486, 488, 594)
mat = pymupdf.Matrix(5, 5)
pix = page.get_pixmap(matrix=mat, clip=clip)
fp = r'D:\DjangoBlog\scrum-ppt\images\fig311_scrum_flow.png'
pix.save(fp)
print(fp, pix.width, 'x', pix.height)
doc.close()
