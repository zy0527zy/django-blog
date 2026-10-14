# 《"栈外"软件系统的数据模型设计说明书》—— comments 部分

> 组号：软工3班8组
> 编写：刘雨婷（计划经理，分支 lyt_branch）
> 负责章节：§3.2.3 comments —— 表 comments_comment、comments_commentreaction
> 依据：`doc/第四周/数据模型类图分析.md` §2.4 + `src/comments/models.py`
> ✅ 字段类型已根据《数据库表结构导出（最终版）》核对完毕。

---

## 3.2.3 comments —— 刘雨婷

comments 应用负责博客的**评论功能**，包含 2 张实体表：
`comments_comment`（评论）、`comments_commentreaction`（评论 Emoji 反应）。

### ① comments_comment（model：Comment）—— 评论表

| 字段 | 类型 | 主键 | 外键 | 说明 |
|---|---|---|---|---|
| id | bigint（自增） | ✅ | — | 评论主键 |
| body | longtext（数据库层无长度限制；应用层 max_length=300 字校验） | — | — | 评论正文内容 |
| creation_time | datetime | — | — | 创建时间（默认当前时间） |
| last_modify_time | datetime | — | — | 最后修改时间 |
| author_id | bigint | — | ✅ → accounts_bloguser.id | 评论作者（一个用户可发多条评论，N:1） |
| article_id | int | — | ✅ → blog_article.id | 评论所属文章（一篇文章可有多条评论，N:1） |
| parent_comment_id | bigint（可空） | — | ✅ → comments_comment.id（自关联） | 父评论：为空=顶层评论；有值=楼中楼回复（0..N:1） |
| is_enable | tinyint(1) | — | — | 是否展示：默认 False=隐藏（待审核），审核通过置 True 后对外展示 |

**索引**：
- `idx_art_parent_enable`：article + parent_comment + is_enable 组合索引，优化评论列表查询；
- `idx_enable_id`：is_enable + id 组合索引，优化侧边栏评论查询。

**model 对应**：`Comment`（`src/comments/models.py`）
- 职责：保存一条评论的内容、作者、所属文章，并通过 `parent_comment` 自关联实现**楼中楼回复**；
- `is_enable` 配合后台审核（admin 批量启用/禁用）控制评论是否对外展示。

**关系重数**（重点：三个外键）：
| 关系 | 关联字段 | 重数 | 关系名 |
|---|---|---|---|
| 评论 → 文章 | comments_comment.article → blog_article | 0..* : 1（N:1） | 一篇文章有多条评论 |
| 评论 → 用户 | comments_comment.author → accounts_bloguser | 0..* : 1（N:1） | 一个用户可发多条评论 |
| 评论 → 评论 | comments_comment.parent_comment → comments_comment（自关联） | 0..* : 0..1 | 楼中楼回复：一条评论可有多个子回复 |

---

### ② comments_commentreaction（model：CommentReaction）—— 评论 Emoji 反应表

| 字段 | 类型 | 主键 | 外键 | 说明 |
|---|---|---|---|---|
| id | bigint（自增） | ✅ | — | 反应记录主键 |
| comment_id | bigint | — | ✅ → comments_comment.id | 被反应的评论（一条评论可被多次表态，N:1） |
| user_id | bigint | — | ✅ → accounts_bloguser.id | 表态的用户（一个用户可对多条评论表态，N:1） |
| reaction_type | varchar(10) | — | — | 表情类型：👍/👎/❤️/😄/🎉/😕/🚀/👀 共 8 种 |
| created_at | datetime | — | — | 表态时间（自动写入） |

**约束**：`unique_together (comment, user, reaction_type)` —— 同一用户对同一评论的同一表情只能点一次，防止重复点赞。

**索引**：`idx_comment_reaction`：comment + reaction_type 组合索引，优化"按评论统计表情"的查询。

**model 对应**：`CommentReaction`（`src/comments/models.py`）
- 职责：记录"哪个用户、对哪条评论、点了什么表情"，支撑评论区 Emoji 互动；
- 视图 `CommentReactionView` 通过 `get_or_create` 实现"再点一次即取消"的切换逻辑。

**关系重数**：
| 关系 | 关联字段 | 重数 | 关系名 |
|---|---|---|---|
| 反应 → 评论 | comments_commentreaction.comment → comments_comment | 0..* : 1（N:1） | 一条评论可有多个表情反应 |
| 反应 → 用户 | comments_commentreaction.user → accounts_bloguser | 0..* : 1（N:1） | 一个用户可对多条评论表态 |

---

### 与整体系统的关系（供 E-R 图使用）

- comments 两张表通过 `article`、`author`、`parent_comment`、`comment`、`user` 等外键与 `blog_article`、`accounts_bloguser`、`comments_comment` 自身相连；
- 其中 reaction 表的 `comment_id` 是 comments 内部关联（reaction→comment），`user_id` 是跨 app 外键；
- **跨 app 外键共 3 条**：comment→article（N:1）、comment→author（N:1）、reaction→user（N:1）；
- 楼中楼自关联是本模块区别于其他 app 的特征结构。
