# -*- coding: utf-8 -*-
import fitz, os

pdf_path = r'C:\Users\刘雨婷\Desktop\实习\作业.pdf'
out_dir = r'D:\DjangoBlog\scrum-ppt\images'
doc = fitz.open(pdf_path)
print('total pages:', doc.page_count)

# 定位包含 图 3.11 的页面
target_pages = []
for i, page in enumerate(doc):
    text = page.get_text()
    if '图 3.11' in text or 'SprintLog' in text or '冲刺订单库' in text:
        target_pages.append(i)
        print('found scrum figure on page index', i)

# 渲染目标页高清图，并抽取该页内嵌图片
for pi in target_pages:
    page = doc[pi]
    # 列出图片
    for img_index, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        base = doc.extract_image(xref)
        ext = base['ext']
        fp = os.path.join(out_dir, f'p{pi}_img{img_index}.{ext}')
        with open(fp, 'wb') as f:
            f.write(base['image'])
        print('saved embedded image:', fp, base['width'], 'x', base['height'])
    # 整页高清渲染，便于裁剪
    mat = fitz.Matrix(3, 3)
    pix = page.get_pixmap(matrix=mat)
    fp = os.path.join(out_dir, f'page_{pi}_render.png')
    pix.save(fp)
    print('saved page render:', fp, pix.width, 'x', pix.height)

doc.close()
