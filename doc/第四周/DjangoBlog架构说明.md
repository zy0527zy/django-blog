# DjangoBlog 架构说明（供组员熟悉 Django 架构用）

> 软工3班8组 · 第四周个人任务参考材料
> 目的：帮助每位组员在开始代码标注前，先建立对 Django 和本项目的整体认识。

---

## 一、Django 的 MVT 架构

Django 采用 **MVT（Model-View-Template）** 架构，和常见的 MVC 类似但叫法不同：

| 层 | Django 中的对应 | 本项目中在哪 |
|----|----------------|--------------|
| **M（Model）** | 数据模型，对应数据库表 | 各 app 的 `models.py` |
| **V（View）** | 业务逻辑，处理请求、查数据 | 各 app 的 `views.py` |
| **T（Template）** | 界面模板，负责渲染 HTML | `src/templates/` |

一次请求的完整流程是：

```
浏览器 → URL 路由(urls.py) → View(views.py) → Model(models.py 查数据库)
                                          → Template(templates) → 返回 HTML
```

## 二、项目目录结构

```
src/
├── manage.py              # Django 命令行入口
├── djangoblog/            # 项目配置（settings/urls/wsgi/admin_site）
├── blog/                  # 博客核心：文章、分类、标签、友链、侧栏、站点配置
├── accounts/              # 用户：BlogUser、登录、注册、忘记密码
├── comments/              # 评论：Comment、评论的 Emoji 反应
├── oauth/                 # 第三方登录：OAuthUser、OAuthConfig
├── servermanager/         # 运维：命令、邮件发送日志
├── plugins/               # 插件系统（文章推荐、阅读时长、SEO 等，动态加载）
├── frontend/              # 前端源码（Vite + Tailwind + Alpine.js/htmx）
├── templates/             # 所有模板（继承/包含体系）
└── whoosh_index/          # 全文搜索索引
```

## 三、各 app 职责

| app | 职责 | 关键文件 |
|-----|------|----------|
| `blog` | 博客核心业务 | `models.py`（Article/Category/Tag 等）、`views.py`（首页/详情/分类/标签/归档等）、`templatetags/blog_tags.py` |
| `accounts` | 用户与认证 | `models.py`（BlogUser，继承 AbstractUser）、`views.py`（登录/注册）、`forms.py` |
| `comments` | 评论 | `models.py`（Comment/CommentReaction）、`views.py` |
| `oauth` | 第三方登录 | `models.py`（OAuthUser/OAuthConfig）、`views.py` |
| `servermanager` | 运维功能 | `models.py`（commands/EmailSendLog） |
| `plugins` | 可插拔功能 | 各插件目录，运行时由 `djangoblog/plugin_manage/` 动态加载 |
| `djangoblog` | 全局配置与路由 | `settings.py`、`urls.py`、`admin_site.py` |

## 四、URL 路由（入口）

主路由在 `djangoblog/urls.py`，通过 `include` 分发给各 app：

- `/` → `blog.urls`（首页、文章、分类、标签、归档、友链）
- `/login/`、`/register/` → `accounts.urls`
- 评论相关 → `comments.urls`
- OAuth 相关 → `oauth.urls`
- `/admin/` → Django 后台
- `/search` → 全文搜索（haystack）

## 五、前端资源（Vite + Tailwind）

前端源码在 `src/frontend/`，用 Vite 构建后输出到 `src/blog/static/blog/dist/`。模板里通过自定义标签 `{% vite_js %}`（`blog/templatetags/vite_tags.py`）按 manifest 加载编译后的 JS/CSS。所以"熟悉 Django 架构"时要注意：**前端是独立构建的**，Django 只负责把编译好的静态资源引入页面。

## 六、几个容易混淆的概念

1. **`blog` app 和"博客"整体**：`blog` 是一个具体的 Django app，不是整个项目；整个项目叫 `djangoblog`。
2. **Model 和数据库表**：`models.py` 里一个类 = 数据库里一张表（如 `Article` → `blog_article`）。
3. **View 和 Template**：View 管"拿到什么数据"，Template 管"长什么样"，两者通过 context 传递数据。
4. **插件 vs app**：`plugins/` 不是标准 app，是运行时动态加载的插件，通过 `plugin_manage` 加载。

---

> 建议组员先按"一次请求怎么走"的思路通读 `djangoblog/urls.py` → 自己负责的 app 的 `views.py` → `models.py`，再动手加注释。
