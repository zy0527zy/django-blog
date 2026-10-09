# -*- coding: utf-8 -*-
import pymupdf

pdf_path = r'C:\Users\刘雨婷\Desktop\实习\作业.pdf'
doc = pymupdf.open(pdf_path)
for i, page in enumerate(doc):
    text = page.get_text()
    head = text[:60].replace('\n', ' ')
    has_scrum = 'Scrum' in text or 'scrum' in text
    has_311 = '3.11' in text
    print(f'page {i}: len={len(text)} scrum={has_scrum} fig311={has_311} | {head}')
doc.close()
