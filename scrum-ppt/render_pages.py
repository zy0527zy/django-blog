# -*- coding: utf-8 -*-
import pymupdf, os

pdf_path = r'C:\Users\刘雨婷\Desktop\实习\作业.pdf'
out_dir = r'D:\DjangoBlog\scrum-ppt\images'
doc = pymupdf.open(pdf_path)
for i, page in enumerate(doc):
    mat = pymupdf.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat)
    fp = os.path.join(out_dir, f'page_{i}.png')
    pix.save(fp)
    print(fp, pix.width, 'x', pix.height)
doc.close()
