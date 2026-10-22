# 软件数据模型设计说明书——blog 数据模型部分

> 负责人：黄梓涵
> 对应章节：3.2.1 blog
> 状态：已依据最终版 MySQL 表结构及 blog/models.py 核对，待组长评审。
> 说明：字段类型、主外键以最终版 MySQL SQL 为准，模型职责依据 blog/models.py。

## 3.2.1 blog 模块数据模型设计

blog 模块负责管理博客文章、分类、标签、友情链接、侧边栏和网站配置等数据。该模块包含六个主要 Model，并通过 Django 自动生成的多对多关联表保存文章与标签之间的关系，共涉及七张数据库表。

##### blog_article（Article）

Article 是博客系统的核心模型，用于保存文章的内容、发布时间、发布状态、浏览量，以及文章与作者、分类、标签之间的关联关系。

| 字段 | 类型 | 主键 | 外键 | 说明 |
|---|---|---|---|---|
| id | int | ✅ |  | 文章唯一标识，继承 BaseModel |
| title | varchar(200) |  |  | 文章标题，唯一 |
| body | longtext |  |  | Markdown 文章正文 |
| pub_time | datetime(6) |  |  | 发布时间 |
| status | varchar(1) |  |  | 文章状态：草稿或已发布 |
| comment_status | varchar(1) |  |  | 是否允许评论 |
| type | varchar(1) |  |  | 普通文章或独立页面 |
| views | int unsigned |  |  | 浏览次数 |
| article_order | int |  |  | 文章排序权重 |
| show_toc | tinyint(1) |  |  | 是否显示文章目录 |
| author_id | bigint |  | ✅ | 指向用户 BlogUser；关联 accounts_bloguser |
| category_id | int |  | ✅ | 指向文章分类 Category；关联 blog_category |
| creation_time | datetime(6) |  |  | 创建时间 |
| last_modify_time | datetime(6) |  |  | 修改时间 |

**Model 对应：** Article，定义在 blog/models.py 中，继承 BaseModel。

**实体关系：**

- BlogUser 与 Article：1:N，关系名称为“撰写”。
- Category 与 Article：1:N，关系名称为“归属分类”。
- Article 与 Tag：N:M，关系名称为“设置标签”。

其中 tags 在 Django 中定义为 ManyToManyField，不作为普通字段直接存储在 blog_article 表中，而是通过 blog_article_tags 中间表实现关联。

##### blog_category（Category）

Category 用于管理文章分类，并支持父子分类形成树形结构。

| 字段 | 类型 | 主键 | 外键 | 说明 |
|---|---|---|---|---|
| id | int | ✅ |  | 分类唯一标识，继承 BaseModel |
| name | varchar(30) |  |  | 分类名称，唯一 |
| slug | varchar(60) |  |  | 用于生成分类 URL 的标识 |
| index | int |  |  | 分类排序值 |
| parent_category_id | int |  | ✅ | 指向同表父分类，可以为空；关联 blog_category；允许 NULL |
| creation_time | datetime(6) |  |  | 创建时间 |
| last_modify_time | datetime(6) |  |  | 修改时间 |

**Model 对应：** Category，定义在 blog/models.py 中，继承 BaseModel。

**实体关系：**

- Category 与 Article：1:N。
- Category 与 Category：自关联，一个分类最多对应一个父分类，一个父分类可以有多个子分类。
- parent_category_id 为空时，该分类可以作为顶级分类。

##### blog_tag（Tag）

Tag 用于保存文章标签，实现文章的多主题标记和按标签检索。

| 字段 | 类型 | 主键 | 外键 | 说明 |
|---|---|---|---|---|
| id | int | ✅ |  | 标签唯一标识，继承 BaseModel |
| name | varchar(30) |  |  | 标签名称，唯一 |
| slug | varchar(60) |  |  | 用于生成标签 URL 的标识 |
| creation_time | datetime(6) |  |  | 创建时间 |
| last_modify_time | datetime(6) |  |  | 修改时间 |

**Model 对应：** Tag，定义在 blog/models.py 中，继承 BaseModel。

**实体关系：**

Tag 与 Article 为 N:M 关系，通过 blog_article_tags 关联表实现。

##### blog_article_tags（文章标签关联表）

该表由 Django 根据 Article.tags 的 ManyToManyField 自动生成，不对应业务代码中独立定义的 Model 类。

| 字段 | 类型 | 主键 | 外键 | 说明 |
|---|---|---|---|---|
| id | bigint | ✅ |  | 关联记录标识 |
| article_id | int |  | ✅ | 指向 blog_article；关联 blog_article |
| tag_id | int |  | ✅ | 指向 blog_tag；关联 blog_tag |

**Model 对应：** Article.tags 的自动生成中间模型。

**实体关系：**

- Article 与 blog_article_tags：1:N。
- Tag 与 blog_article_tags：1:N。

这两个一对多关系共同实现 Article 与 Tag 之间的多对多关系。数据库已设置 (article_id, tag_id) 联合唯一约束。

##### blog_links（Links）

Links 保存友情链接的基本信息及其展示控制参数。

| 字段 | 类型 | 主键 | 外键 | 说明 |
|---|---|---|---|---|
| id | bigint | ✅ |  | 链接唯一标识 |
| name | varchar(30) |  |  | 链接名称，唯一 |
| link | varchar(200) |  |  | 链接地址 |
| sequence | int |  |  | 显示顺序，唯一 |
| is_enable | tinyint(1) |  |  | 是否启用 |
| show_type | varchar(1) |  |  | 展示位置类型 |
| last_mod_time | datetime(6) |  |  | 修改时间 |
| creation_time | datetime(6) |  |  | 创建时间 |

**Model 对应：** Links。

**职责：** 维护友情链接名称、地址、排序以及展示状态。

**关系说明：** 当前 Model 中没有直接声明指向其他业务实体的外键。

##### blog_sidebar（SideBar）

SideBar 保存博客侧边栏中可以自定义展示的内容。

| 字段 | 类型 | 主键 | 外键 | 说明 |
|---|---|---|---|---|
| id | bigint | ✅ |  | 侧边栏记录标识 |
| name | varchar(100) |  |  | 侧边栏名称 |
| content | longtext |  |  | 自定义内容 |
| sequence | int |  |  | 展示顺序，唯一 |
| is_enable | tinyint(1) |  |  | 是否启用 |
| last_mod_time | datetime(6) |  |  | 修改时间 |
| creation_time | datetime(6) |  |  | 创建时间 |

**Model 对应：** SideBar。

**职责：** 管理侧边栏内容、排序顺序及启用状态。

**关系说明：** 当前 Model 中没有直接声明指向其他业务实体的外键。

##### blog_blogsettings（BlogSettings）

BlogSettings 用于保存博客网站的全局设置。模型通过 clean() 提供单实例校验，管理后台限制重复添加，但数据库没有强制单记录唯一约束。

| 字段 | 类型 | 主键 | 外键 | 说明 |
|---|---|---|---|---|
| id | bigint | ✅ |  | 配置记录标识 |
| site_name | varchar(200) |  |  | 网站名称 |
| site_description | longtext |  |  | 网站介绍 |
| site_seo_description | longtext |  |  | SEO 描述 |
| site_keywords | longtext |  |  | 网站关键词 |
| article_sub_length | int |  |  | 文章摘要长度 |
| sidebar_article_count | int |  |  | 侧边栏文章显示数量 |
| sidebar_comment_count | int |  |  | 侧边栏评论显示数量 |
| article_comment_count | int |  |  | 文章评论显示数量 |
| show_google_adsense | tinyint(1) |  |  | 是否显示广告 |
| google_adsense_codes | longtext |  |  | 广告代码；允许 NULL |
| open_site_comment | tinyint(1) |  |  | 是否允许全站评论 |
| beian_code | varchar(2000) |  |  | 网站备案号；允许 NULL |
| analytics_code | longtext |  |  | 网站统计代码 |
| show_gongan_code | tinyint(1) |  |  | 是否显示公安备案 |
| gongan_beiancode | longtext |  |  | 公安备案号；允许 NULL |
| global_footer | longtext |  |  | 全局底部内容；允许 NULL |
| global_header | longtext |  |  | 全局头部内容；允许 NULL |
| comment_need_review | tinyint(1) |  |  | 评论是否需要审核 |
| color_scheme | varchar(20) |  |  | 主题配色 |

**Model 对应：** BlogSettings。

**职责：** 保存整个网站的通用配置，包括站点基本信息、界面主题、评论设置、侧边栏数量以及备案和统计信息。

**关系说明：** 当前 Model 中没有直接声明指向其他业务实体的外键。

##### blog 模块实体关系汇总

| 实体 A | 实体 B | 关系重数 | 关系名称 |
|---|---|---|---|
| BlogUser | Article | 1:N | 撰写 |
| Category | Article | 1:N | 分类包含文章 |
| Article | Tag | N:M | 设置标签 |
| Article | blog_article_tags | 1:N | 文章标签关联 |
| Tag | blog_article_tags | 1:N | 标签文章关联 |
| Category | Category | 1:N 自关联 | 父子分类 |

以上重数描述关系类型，实际数据允许为零的情况应结合外键可空性与业务约束分析。

##### 数据库结构核对结论

本节已依据《数据库表结构导出（最终版）》完成 blog 七张表的 MySQL 字段类型、主键、外键和可空性核对，并结合 `src/blog/models.py` 说明 Model 对应关系及业务职责。

主要约束与索引如下：

1. `blog_article.title` 具有唯一约束，`views` 具有非负约束，并设置文章查询相关组合索引。
2. `blog_category.name` 和 `blog_tag.name` 具有唯一约束，两表的 `slug` 字段设有索引。
3. `blog_article_tags` 对 `(article_id, tag_id)` 设置联合唯一约束，防止重复绑定。
4. `blog_links.name` 与 `blog_links.sequence` 具有唯一约束。
5. `blog_sidebar.sequence` 具有唯一约束。
6. `blog_blogsettings` 没有数据库级单记录约束。Model 的 `clean()` 和管理后台提供相应限制，但普通 `save()` 不会自动调用 `full_clean()`。

本节字段类型为实际 MySQL 数据类型，和 Django ORM 中的字段声明类型应加以区分。

状态：已完成数据库结构核对，待团队评审。
