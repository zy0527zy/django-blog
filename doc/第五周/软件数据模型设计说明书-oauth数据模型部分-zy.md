# 《"栈外"软件系统的数据模型设计说明书》

> 组号：软工3班8组
> 小组成员：张月、黄梓涵、侍文博、刘雨婷、谢承志、朱亮宇
> 依据模板：`文档模板-软件数据模型设计说明书模板.docx`
> 说明：第五周小组主交付物，最终放入在线项目 master 分支 doc 目录。

---

## 1 软件系统概述
> 【张月】简要介绍「栈外」博客系统解决的主要问题（系统定位、目标用户、核心价值）。

（待填写）

---

## 2 功能与数据分析
> 【黄梓涵主笔 + 侍文博协助】按主要功能罗列系统功能，说明每个功能需要处理的主要数据对象。
> 各成员先各自提供自己 app 的功能清单，开发经理汇总成统一口径。

（待填写）

---

## 3 数据模型设计

### 3.1 数据库整体 E-R 图
> 【黄梓涵主画 + 侍文博协助】汇总各 app 实体与跨 app 外键，画整体 E-R 图，标注关系重数（1:1 / 1:N / N:M）与关系名。图片插入此处。

**跨 app 外键关系提示**（画图时务必覆盖）：
| 关系 | 说明 |
|---|---|
| blog_article.author → accounts_bloguser | 文章作者（N:1） |
| blog_article.category → blog_category | 文章分类（N:1） |
| blog_article.tags ↔ blog_tag（blog_article_tags） | 文章标签（N:M） |
| comments_comment.article → blog_article | 评论所属文章（N:1） |
| comments_comment.author → accounts_bloguser | 评论作者（N:1） |
| comments_comment.parent_comment → comments_comment | 楼中楼自关联（0..N:1） |
| comments_commentreaction.comment → comments_comment | 评论点赞（N:1） |
| oauth_oauthuser.author → accounts_bloguser | 第三方账号绑定（0..1:1） |

（待插入 E-R 图）

### 3.2 各实体表结构与 model 对应（按 app 分工）

> 统一格式：每个实体给出「①表结构表」+「②model 对应说明」。字段类型可引用朱亮宇导出的《数据库表结构导出.md》。

#### 3.2.1 blog —— 黄梓涵
表：blog_article、blog_category、blog_tag、blog_links、blog_sidebar、blog_blogsettings、blog_article_tags

（同格式逐个填）

#### 3.2.2 accounts —— 侍文博
表：accounts_bloguser（BlogUser，继承 AbstractUser）、accounts_bloguser_groups、accounts_bloguser_user_permissions

（同格式逐个填）

#### 3.2.3 comments —— 刘雨婷
表：comments_comment（Comment）、comments_commentreaction（CommentReaction）

（同格式逐个填，重点写清 article/author/parent_comment 三个外键）

#### 3.2.4 oauth —— 谢承志
表：oauth_oauthuser（OAuthUser）、oauth_oauthconfig（OAuthConfig）

##### oauth_oauthuser（model: OAuthUser）
| 字段 | 类型 | 主键 | 外键 | 说明 |
| ---- | ---- | ---- | ---- | ---- |
| id | bigint | ✅ |  | 主键ID，自增 |
| openid | varchar(50) |  |  | 第三方平台的用户唯一标识（如 GitHub 的 id、QQ 的 openid） |
| nickname | varchar(50) |  |  | 第三方平台昵称 |
| token | varchar(150) |  |  | 第三方访问令牌，可空（用于调用第三方接口） |
| picture | varchar(350) |  |  | 用户头像链接，可空 |
| type | varchar(50) |  |  | 第三方平台类型（weibo/google/github/facebook/qq） |
| email | varchar(50) |  |  | 第三方平台邮箱，可空（部分平台不公开邮箱） |
| metadata | longtext |  |  | 第三方返回的原始 JSON 元数据，可空 |
| author_id | bigint |  | ✅ | 绑定的本地用户，外键 → accounts_bloguser.id，可空（未绑定时为 null） |
| creation_time | datetime(6) |  |  | 创建时间，Django default=now：新增记录自动写入当前时间 |
| last_modify_time | datetime(6) |  |  | 最后修改时间，Django default=now：默认当前时间 |

**model 对应**: OAuthUser — 数据：第三方授权用户信息（openid/nickname/token/picture/type/email/metadata）；职责：存储从第三方平台获取并映射的用户信息，通过 author 外键与本地 BlogUser 建立「可选绑定」。关系重数：author（OAuthUser → BlogUser）为 **0..1 : 1**——第三方账号可选绑定至多 1 个本地用户（`null=True`），未绑定时 author 为空，绑定后经 `oauth/authorize` 或 `emailconfirm` 流程写入；一个本地 BlogUser 可被多个第三方账号绑定。

##### oauth_oauthconfig（model: OAuthConfig）
| 字段 | 类型 | 主键 | 外键 | 说明 |
| ---- | ---- | ---- | ---- | ---- |
| id | bigint | ✅ |  | 主键ID，自增 |
| type | varchar(10) |  |  | 平台类型，受 TYPE 枚举约束（weibo/google/github/facebook/qq） |
| appkey | varchar(200) |  |  | 平台申请的 AppKey |
| appsecret | varchar(200) |  |  | 平台申请的 AppSecret |
| callback_url | varchar(200) |  |  | OAuth 回调地址 |
| is_enable | tinyint(1) |  |  | 是否启用该平台登录，Django BooleanField，布尔 0/1，默认 True |
| creation_time | datetime(6) |  |  | 创建时间，Django default=now：新增记录自动写入当前时间 |
| last_modify_time | datetime(6) |  |  | 最后修改时间，Django default=now：默认当前时间 |

**model 对应**: OAuthConfig — 数据：各第三方平台的接入配置；职责：存储 AppKey / AppSecret / 回调地址及启用状态，供 `oauthmanager.py` 各平台管理器读取、供模板标签 `load_oauth_applications` 渲染登录按钮；无外键，与其它实体无关联、无关系重数（通过 `clean()` 约束同一 type 仅允许一条记录）。

#### 3.2.5 servermanager —— 朱亮宇
表：servermanager_commands（commands）、servermanager_emailsendlog（EmailSendLog）

（同格式逐个填）

### 3.3 实体与 model 的对应关系汇总
> 【全员提供 + 张月汇总】一张总表。

| 实体表 | model 类 | 所在 app | 职责 |
|---|---|---|---|
| oauth_oauthuser | OAuthUser | oauth | 存储第三方授权用户信息，与本地用户可选绑定 |
| oauth_oauthconfig | OAuthConfig | oauth | 存储各第三方平台的接入配置与启用状态 |
