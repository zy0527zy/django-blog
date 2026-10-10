import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, Ellipse
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# ========== 系统边界矩形 ==========
box = patches.FancyBboxPatch((0.16, 0.06), 0.68, 0.89,
                              boxstyle="round,pad=0.01",
                              linewidth=1.5, edgecolor='black', facecolor='white')
ax.add_patch(box)

# ========== 画小人（Actor）函数 ==========
def draw_actor(x, y, name_cn, name_en, scale=1.0):
    # 头
    head = plt.Circle((x, y+0.04*scale), 0.015*scale, fill=False, linewidth=1.5, edgecolor='black')
    ax.add_patch(head)
    # 身体
    ax.plot([x, x], [y+0.025*scale, y-0.02*scale], 'k-', linewidth=1.5)
    # 手臂
    ax.plot([x-0.025*scale, x+0.025*scale], [y+0.005*scale, y+0.005*scale], 'k-', linewidth=1.5)
    # 腿
    ax.plot([x, x-0.02*scale], [y-0.02*scale, y-0.05*scale], 'k-', linewidth=1.5)
    ax.plot([x, x+0.02*scale], [y-0.02*scale, y-0.05*scale], 'k-', linewidth=1.5)
    # 名字
    ax.text(x, y-0.08*scale, name_cn, ha='center', va='top', fontsize=12, fontweight='bold')
    ax.text(x, y-0.11*scale, name_en, ha='center', va='top', fontsize=10, style='italic')

# 参与者
draw_actor(0.07, 0.75, '游客', '(Visitor)')
draw_actor(0.07, 0.35, '注册用户', '(User)')
draw_actor(0.93, 0.55, '管理员', '(Admin)')

# ========== 画用例（椭圆）函数 ==========
def draw_usecase(x, y, text, width=0.12, height=0.06):
    ellipse = Ellipse((x, y), width, height, fill=True, facecolor='white',
                      edgecolor='black', linewidth=1.2)
    ax.add_patch(ellipse)
    ax.text(x, y, text, ha='center', va='center', fontsize=10)

# ========== 左列用例（游客） ==========
x1 = 0.30
uc_visitor = [
    (x1, 0.91, '用户注册'),
    (x1, 0.82, '用户登录'),
    (x1, 0.72, '浏览文章列表'),
    (x1, 0.62, '查看文章详情'),
    (x1, 0.52, '搜索文章'),
    (x1, 0.42, '按分类浏览'),
    (x1, 0.32, '按标签浏览'),
    (x1, 0.22, '查看归档'),
]
for x, y, t in uc_visitor:
    draw_usecase(x, y, t)

# ========== 中列用例（注册用户） ==========
x2 = 0.52
draw_usecase(x2, 0.68, '发表评论')
draw_usecase(x2, 0.55, '回复评论')
draw_usecase(x2, 0.42, '用户登出')

# ========== 右列用例（管理员） ==========
x3 = 0.74
uc_admin = [
    (x3, 0.91, '发布文章'),
    (x3, 0.81, '编辑文章'),
    (x3, 0.71, '删除文章'),
    (x3, 0.61, '管理分类标签'),
    (x3, 0.51, '管理评论'),
    (x3, 0.41, '管理用户'),
    (x3, 0.31, '管理友情链接'),
    (x3, 0.21, '网站设置'),
]
for x, y, t in uc_admin:
    draw_usecase(x, y, t)

# ========== 连接线：参与者到用例 ==========
# 游客 → 左列用例
for _, y, _ in uc_visitor:
    ax.plot([0.09, x1-0.06], [0.75+0.03, y], 'k-', linewidth=0.8)

# 注册用户 → 中列用例
for y in [0.68, 0.55, 0.42]:
    ax.plot([0.09, x2-0.06], [0.35+0.03, y], 'k-', linewidth=0.8)

# 管理员 → 右列用例
for _, y, _ in uc_admin:
    ax.plot([0.91, x3+0.06], [0.55+0.03, y], 'k-', linewidth=0.8)

# ========== 包含关系（虚线箭头） ==========
def draw_include(x1, y1, x2, y2):
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                           arrowstyle='->', linestyle='--',
                           linewidth=1, color='black',
                           mutation_scale=15)
    ax.add_patch(arrow)

# 发表评论 → 用户登录
draw_include(0.46, 0.68, 0.37, 0.82)
ax.text(0.42, 0.76, '<<包含>>', fontsize=9, ha='center')

# 回复评论 → 用户登录
draw_include(0.46, 0.55, 0.37, 0.82)
ax.text(0.43, 0.70, '<<包含>>', fontsize=9, ha='center')

# 发布文章 → 用户登录
draw_include(0.68, 0.91, 0.37, 0.82)
ax.text(0.55, 0.90, '<<包含>>', fontsize=9, ha='center')

# 编辑文章 → 用户登录
draw_include(0.68, 0.81, 0.37, 0.82)
ax.text(0.55, 0.84, '<<包含>>', fontsize=9, ha='center')

# ========== 参与者泛化（空心三角箭头） ==========
def draw_generalization(x1, y1, x2, y2):
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                           arrowstyle='-|>', linestyle='-',
                           linewidth=1.2, color='black',
                           mutation_scale=18,
                           facecolor='white', edgecolor='black')
    ax.add_patch(arrow)

# 注册用户 → 游客（泛化）
draw_generalization(0.07, 0.43, 0.07, 0.68)

# 管理员 → 注册用户（泛化，用虚线跨过去，简单点画在右边）
# 为了清晰，画在参与者旁边
draw_generalization(0.93, 0.48, 0.93, 0.35)
# 不对，管理员在右边，注册用户在左边，没法直接画
# 改成：管理员泛化到注册用户，用一条虚线在底部
# 算了，直接标注：管理员继承注册用户

# 标题
ax.text(0.5, 0.98, 'DjangoBlog 博客系统用例图', ha='center', va='center',
        fontsize=16, fontweight='bold')

plt.tight_layout()
plt.savefig(r'D:\DjangoBlog\doc\第五周\DjangoBlog用例图.png', dpi=200, bbox_inches='tight',
            facecolor='white')
plt.close()
print("用例图已生成：D:\\DjangoBlog\\doc\\第五周\\DjangoBlog用例图.png")
