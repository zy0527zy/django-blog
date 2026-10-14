# ***开源软件系统的泛读报告

> 组号：8
> 小组成员：张月、黄梓涵、侍文博、刘雨婷、谢承志、朱亮宇
>
> **填写说明：每人只写自己负责的板块，提交自己那部分的 md（命名：`开源软件泛读报告-<部分>-<姓名>.md`），只保留自己的内容，不要并入他人的内容，最终由张月统一合并。** 各板块负责人已标注在标题下方。

---

## 1. 开源软件的功能描述

### 1.1 用例图和用例图说明
> 负责人：各 app 负责人（blog=黄梓涵、accounts=侍文博、comments=刘雨婷、oauth=谢承志、servermanager/plugins=朱亮宇）；系统级用例与整体用例图=张月；核心流程整合=黄梓涵、侍文博（开发经理）

（绘制系统用例图，并对每个用例给出用例说明。用例按 app 划分，各负责人写自己 app 的用例。）

**用例说明格式（每个用例一条，可复制多份）：**

| 项目 | 内容 |
|------|------|
| 用例名称 | （如：发布文章）|
| 参与者（Actor）| （如：登录用户）|
| 前置条件 | |
| 后置条件 | |
| 基本流程 | 1. …<br>2. …<br>3. … |
| 扩展流程 | 1a. 若…则… |
| 顺序图 | （插入该用例的顺序图）|

---

#### 【朱亮宇负责部分】servermanager / plugins 应用用例

**（1）用例图（servermanager 与 plugins）**

![servermanager与plugins用例图](imgs/servermanager-plugins-usecase-zly.png)

**（2）用例说明**

**UC-SM-1 微信机器人文章检索**

| 项目 | 内容 |
|------|------|
| 用例名称 | 微信机器人文章检索 |
| 参与者（Actor）| 微信用户 |
| 前置条件 | 机器人服务已运行（Werobot token 已配置）、微信公众号已接入；博客已有文章数据 |
| 后置条件 | 用户收到文章图文消息或提示文本；用户会话状态已更新 |
| 基本流程 | 1. 用户向公众号发送指令消息（?关键字 / category / recent / help）<br>2. 微信服务器将消息转发到 /robot 回调，robot 读取该用户会话<br>3. 按正则过滤器匹配指令并分发<br>4. BlogApi 查询数据：?关键字走 Haystack 检索，category 取分类列表，recent 取最新文章（均最多 8 条）<br>5. convert_to_article_reply 组装图文消息（首图/标题/摘要/文章链接）<br>6. 回复用户 |
| 扩展流程 | 4a. 消息不匹配任何指令 → 转入 UC-SM-2 智能问答或 UC-SM-3 管理员命令流程<br>4b. 关键字未检索到结果 → 回复"没有找到相关文章。"<br>4c. recent 暂无已发布文章 → 回复"暂时还没有文章" |
| 顺序图 | 见下图 |

![顺序图-01-微信机器人文章检索](imgs/servermanager-plugins-sequence-01-wechat-article-search-zly.png)

**UC-SM-2 微信机器人智能问答**

| 项目 | 内容 |
|------|------|
| 用例名称 | 微信机器人智能问答 |
| 参与者（Actor）| 微信用户 |
| 前置条件 | 已配置 OPENAI_API_KEY 且网络可达 OpenAI 接口 |
| 后置条件 | 用户收到 AI 回复文本 |
| 基本流程 | 1. 用户发送未被任何指令过滤器匹配的消息<br>2. 进入默认处理器 echo，构造 MessageHandler 并读取会话<br>3. 判定为非管理员消息 → ChatGPT.chat(消息内容)<br>4. 调用 OpenAI gpt-3.5-turbo 生成回复<br>5. 回复文本返回给用户 |
| 扩展流程 | 3a. OpenAI 接口调用异常 → 记录错误日志，回复"服务器出错了"<br>3b. 该用户处于管理员模式 → 转入 UC-SM-3 流程 |
| 顺序图 | 见下图 |

![顺序图-02-微信机器人智能问答](imgs/servermanager-plugins-sequence-02-wechat-ai-qa-zly.png)

**UC-SM-3 微信机器人远程执行服务器命令**

| 项目 | 内容 |
|------|------|
| 用例名称 | 微信机器人远程执行服务器命令 |
| 参与者（Actor）| 微信管理员 |
| 前置条件 | 已在 settings 配置 WXADMIN 管理员密码；运维命令已由后台维护（见 UC-SM-4）|
| 后置条件 | 指定服务器命令被执行，输出结果返回微信；管理员状态随会话保存 |
| 基本流程 | 1. 管理员发送 ADMIN → 会话标记 isAdmin=True，提示"输入管理员密码"<br>2. 输入密码：做两次 SHA256 哈希后与 settings.WXADMIN 比对<br>3. 校验通过 → 标记 isPasswordSet=True，提示输入命令（helpme 可看命令清单）<br>4. 输入命令 → 暂存到会话 → 回复"确认执行: xxx 命令?"<br>5. 回复 Y → CommandHandler 按标题在 commands 表匹配命令 → os.popen 执行 → 返回输出<br>6. 发送 EXIT → 清空管理员状态，退出管理员模式 |
| 扩展流程 | 2a. 密码错误 → 错误计数 +1，累计满 3 次重置管理员状态并提示"超过验证次数"<br>5a. 命令标题不存在 → 提示"未找到相关命令，请输入hepme获得帮助。"<br>5b. 未回复 Y 而输入新文本 → 覆盖暂存的待执行命令，再次要求确认<br>5c. 命令执行抛异常 → 回复"命令执行出错!" |
| 顺序图 | 见下图 |

![顺序图-03-微信机器人远程执行命令](imgs/servermanager-plugins-sequence-03-wechat-remote-command-zly.png)

**UC-SM-4 运维命令维护**

| 项目 | 内容 |
|------|------|
| 用例名称 | 运维命令维护 |
| 参与者（Actor）| 站点管理员（超级用户）|
| 前置条件 | 以超级用户身份登录 Django 后台 |
| 后置条件 | commands 表更新；机器人重启后使用最新命令清单 |
| 基本流程 | 1. 打开后台「命令」管理<br>2. 新增/修改/删除命令（命令标题、命令内容、命令描述）<br>3. 保存写入 commands 表<br>4. 机器人进程（重）启动时 CommandHandler 加载全部命令<br>5. helpme 帮助列表与远程命令执行随即使用最新数据 |
| 扩展流程 | 5a. 机器人进程未重启 → 仍使用启动时加载的旧命令列表 |
| 顺序图 | 见下图 |

![顺序图-04-运维命令维护](imgs/servermanager-plugins-sequence-04-command-maintenance-zly.png)

**UC-SM-5 邮件发送日志查看**

| 项目 | 内容 |
|------|------|
| 用例名称 | 邮件发送日志查看 |
| 参与者（Actor）| 站点管理员（超级用户）|
| 前置条件 | 系统已在注册验证、OAuth 绑定、评论通知等场景触发过邮件发送 |
| 后置条件 | 管理员掌握每次邮件发送的收件人、内容与结果 |
| 基本流程 | 1. 邮件信号处理器在每次发送后自动写入 EmailSendLog（收件人/标题/内容/发送结果）<br>2. 管理员登录后台打开「邮件发送log」<br>3. 列表按创建时间倒序展示标题、收件邮箱、发送结果、创建时间<br>4. 查看某条记录的完整内容与结果 |
| 扩展流程 | 1a. 邮件发送异常 → 同样写入日志，send_result=False<br>4a. 后台禁止手动新增日志（has_add_permission=False），日志只读 |
| 顺序图 | 见下图 |

![顺序图-05-邮件发送日志查看](imgs/servermanager-plugins-sequence-05-email-log-view-zly.png)

**UC-SM-6 微信会话缓存存取**

| 项目 | 内容 |
|------|------|
| 用例名称 | 微信会话缓存存取 |
| 参与者（Actor）| 微信用户（间接触发）、系统 |
| 前置条件 | Django 缓存后端已配置（默认 LocMemCache，可切换 Redis）|
| 后置条件 | 用户会话状态（管理员标记/待执行命令/计数等）被持久保存 |
| 基本流程 | 1. 机器人启动时检测缓存可用性（写入并回读测试键）<br>2. 缓存可用 → 会话存储设为 MemcacheStorage（key 前缀 ws_）<br>3. 用户消息到达 → 按用户 openid 读取会话，JSON 反序列化<br>4. 消息处理完毕后写回会话，JSON 序列化 |
| 扩展流程 | 1a. 缓存不可用 → 删除遗留会话文件，降级为 FileStorage 文件存储<br>3a. 读取异常/无会话记录 → 新建空会话对象，正常继续处理<br>2a. 降级为文件存储后缓存恢复 → 需重启进程才会切回缓存存储 |
| 顺序图 | 见下图 |

![顺序图-06-微信会话缓存存取](imgs/servermanager-plugins-sequence-06-wechat-session-cache-zly.png)

**UC-PL-1 插件加载与启停**

| 项目 | 内容 |
|------|------|
| 用例名称 | 插件加载与启停 |
| 参与者（Actor）| 站点管理员 |
| 前置条件 | 插件目录结构完整（plugins/<插件名>/plugin.py 存在模块级 plugin 实例）|
| 后置条件 | 启用的插件完成钩子注册，功能随钩子自动生效 |
| 基本流程 | 1. 管理员在 settings.py 的 ACTIVE_PLUGINS 列表中决定启用哪些插件（当前启用 8 个）<br>2. 重启服务，Django 应用就绪后调用 load_plugins()<br>3. 逐个 import plugins.<插件名>.plugin，取出模块级 plugin 实例<br>4. 实例化时 BasePlugin.__init__ 依次调用 init_plugin()（可校验配置）与 register_hooks()（注册钩子回调）<br>5. 加载完成后插件在对应钩子上开始工作 |
| 扩展流程 | 3a. 插件目录或 plugin.py 缺失 → 跳过并记录日志<br>4a. 插件配置无效（如 Cloudflare 未配置凭证）→ 插件自我禁用（enabled=False）<br>1a. 修改 ACTIVE_PLUGINS 后需重启服务才生效 |
| 顺序图 | 见下图 |

![顺序图-07-插件加载与启停](imgs/servermanager-plugins-sequence-07-plugin-load-zly.png)

**UC-PL-2 文章内容钩子增强**

| 项目 | 内容 |
|------|------|
| 用例名称 | 文章内容钩子增强 |
| 参与者（Actor）| 访客 |
| 前置条件 | 版权、阅读时间、外部链接、图片懒加载插件已启用 |
| 后置条件 | 页面正文 HTML 被各插件依次增强后输出 |
| 基本流程 | 1. 访客打开文章详情页<br>2. 模板调用 render_article_content / custom_markdown 渲染正文<br>3. Markdown 转 HTML<br>4. hooks.apply_filters 沿 the_content 过滤器链按注册顺序依次执行：版权声明 → 阅读时间 → 外部链接 → 图片懒加载<br>5. 增强后的 HTML 渲染展示 |
| 扩展流程 | 4a. 摘要模式（首页/列表页）→ 版权声明与阅读时间插件跳过<br>4b. 链接已有 target 属性或为站内链接 → 外链插件跳过该链接<br>4c. 内容中没有 img 标签 → 图片插件原样返回 |
| 顺序图 | 见下图 |

![顺序图-08-文章内容钩子增强](imgs/servermanager-plugins-sequence-08-content-hooks-zly.png)

**UC-PL-3 相关文章推荐**

| 项目 | 内容 |
|------|------|
| 用例名称 | 相关文章推荐 |
| 参与者（Actor）| 访客 |
| 前置条件 | 文章推荐插件已启用；当前文章已归入分类、可带标签 |
| 后置条件 | 文章详情页底部展示"相关推荐"组件 |
| 基本流程 | 1. 访客打开文章详情页<br>2. 视图触发 article_detail_load 钩子<br>3. 插件 get_recommendations(article, 8)：先按相同标签检索已发布文章（浏览量降序）<br>4. 数量不足 → 按同分类补齐<br>5. 仍不足 → 取全站热门（浏览量降序）补齐<br>6. 过滤空标题后写入 context，模板渲染底部组件（bottom_widget.html） |
| 扩展流程 | 5a. 三级策略均无候选 → 不渲染推荐组件（返回 None）|
| 顺序图 | 见下图 |

![顺序图-09-相关文章推荐](imgs/servermanager-plugins-sequence-09-article-recommendation-zly.png)

**UC-PL-4 SEO 元数据生成**

| 项目 | 内容 |
|------|------|
| 用例名称 | SEO 元数据生成 |
| 参与者（Actor）| 访客（含搜索引擎爬虫）|
| 前置条件 | SEO 优化器插件已启用 |
| 后置条件 | 页面 <head> 中携带 Open Graph 标签与 JSON-LD 结构化数据 |
| 基本流程 | 1. 页面渲染时执行 head_meta 过滤器<br>2. SEO 插件按 view_name 判断页面类型<br>3. 文章页 → Open Graph + Article 类型 JSON-LD；分类/标签/作者页 → BreadcrumbList 面包屑；其余页面 → WebSite + SearchAction<br>4. 生成结果追加到已有 meta 内容后输出 |
| 扩展流程 | 3a. 未识别页面类型 → 生成默认 WebSite 结构化数据<br>3b. 文章无首图 → JSON-LD 中移除 image 字段 |
| 顺序图 | 见下图 |

![顺序图-10-SEO元数据生成](imgs/servermanager-plugins-sequence-10-seo-metadata-zly.png)

**UC-PL-5 CDN 缓存自动清除**

| 项目 | 内容 |
|------|------|
| 用例名称 | CDN 缓存自动清除 |
| 参与者（Actor）| 系统（模型保存信号）|
| 前置条件 | Cloudflare 缓存插件已启用且凭证（Zone ID / API Token）配置有效 |
| 后置条件 | 受影响页面的 CDN 缓存被清除，用户可看到最新内容 |
| 基本流程 | 1. 作者/管理员保存文章，或新评论通过审核发布<br>2. post_save 信号触发 CloudflareCacheHandler<br>3. 收集需清除的 URL（文章页/首页/分类页/标签页/RSS）<br>4. 按 30 条/批调用 CloudflareAPI.purge_urls 清除<br>5. 清除失败仅记录日志，不影响主业务流程 |
| 扩展流程 | 3a. 仅浏览量更新（update_fields={'views'}）→ 跳过，避免高频清缓存<br>2a. 评论未通过审核（is_enable=False）→ 跳过<br>1a. 配置 CLOUDFLARE_PURGE_ON_STARTUP=true → 应用启动后由后台线程清理全站缓存 |
| 顺序图 | 见下图 |

![顺序图-11-CDN缓存自动清除](imgs/servermanager-plugins-sequence-11-cdn-cache-purge-zly.png)

**UC-PL-6 文章浏览量统计**

| 项目 | 内容 |
|------|------|
| 用例名称 | 文章浏览量统计 |
| 参与者（Actor）| 访客 |
| 前置条件 | 浏览量统计插件已启用 |
| 后置条件 | 文章 views 字段 +1，用于热门排序与推荐 |
| 基本流程 | 1. 访客打开文章详情页<br>2. 正文获取完成，触发 after_article_body_get 钩子<br>3. ViewCountPlugin.record_view → article.viewed()<br>4. views += 1，以 update_fields=['views'] 保存 |
| 扩展流程 | 4a. post_save 处理器识别"仅浏览量更新" → 跳过缓存清理与搜索引擎推送 |
| 顺序图 | 见下图 |

![顺序图-12-文章浏览量统计](imgs/servermanager-plugins-sequence-12-view-count-zly.png)

### 1.2 数据流图和数据字典
> 负责人：数据流图=谢承志；数据字典=朱亮宇

- **系统数据流图**：（谢承志绘制整体数据流图，标明数据加工、数据流、数据存储、外部实体）
- **主要数据条目的数据字典**：（朱亮宇对主要数据条目逐条给出名称、含义、类型/格式、来源、去向）

#### 【朱亮宇负责部分】主要数据条目的数据字典

> 说明：数据条目依据《数据库表结构导出（最终版）》（第五周，全库 24 张表）与《软件数据模型设计说明书（最终版）》整理；完整字段级清单见上述文档，本表逐条给出名称、含义、类型/格式、来源、去向，覆盖全部 24 张表（16 张业务表 + 8 张 Django 内置支撑表）。

**（一）业务数据条目（16 张业务表）**

| 数据条目 | 含义 | 类型/格式 | 来源 | 去向 |
|----------|------|-----------|------|------|
| blog_article（文章/页面）| 站点文章与独立页面，含正文、发布状态、类型与浏览量 | 表：id int 主键；title varchar(200) 唯一；body longtext（Markdown）；pub_time datetime；status char(1)〔d 草稿/p 发布〕；comment_status char(1)〔o 开/c 关〕；type char(1)〔a 文章/p 页面〕；views int unsigned（≥0，CHECK 约束）；article_order int；show_toc bool；author_id → accounts_bloguser；category_id → blog_category；creation_time / last_modify_time datetime | 后台「文章」管理（管理员以 Markdown 撰写/编辑、批量改状态）；浏览量由浏览量统计插件在访问时自增 | 首页/分类页/标签页/作者页/归档页/详情页渲染；Haystack 站内搜索与微信机器人检索；相关推荐、SEO、CDN 缓存插件读取；RSS |
| blog_category（文章分类）| 文章分类，支持父子结构形成多级分类树 | 表：id int 主键；name varchar(30) 唯一；slug varchar(60)；index int（排序）；parent_category_id → blog_category（自关联，可空）；creation_time / last_modify_time datetime | 后台「文章分类」管理（保存时自动生成 slug）；文章编辑时选择归类 | 站点导航、分类归档页；文章详情面包屑；机器人 category 指令；推荐插件分类兜底 |
| blog_tag（文章标签）| 文章标签，用于聚合同类主题文章 | 表：id int 主键；name varchar(30) 唯一；slug varchar(60)；creation_time / last_modify_time datetime | 后台「文章标签」管理；文章编辑时新建/选择标签 | 标签归档页；文章详情标签展示；SEO og:tag；推荐插件标签匹配 |
| blog_article_tags（文章-标签关联）| 文章与标签的多对多中间表 | 表：id bigint；article_id → blog_article；tag_id → blog_tag；UNIQUE(article_id, tag_id) | Django ORM 由 Article.tags 多对多自动维护 | 标签聚合查询（JOIN）；标签页与推荐插件的关联检索 |
| blog_links（友情链接）| 站点友情链接，含展示位置与排序 | 表：id bigint；name varchar(30) 唯一；link varchar(200)；sequence int 唯一（排序）；is_enable bool；show_type char(1)〔i 首页/l 列表/p 文章/a 全部/s 滑动〕；creation_time / last_mod_time datetime | 后台「友情链接」管理 | 首页/列表页等位置的友链区域（按 is_enable 与 show_type 过滤）|
| blog_sidebar（侧边栏）| 侧边栏自定义内容块（HTML）| 表：id bigint；name varchar(100)；content longtext（HTML）；sequence int 唯一；is_enable bool；creation_time / last_mod_time datetime | 后台「侧边栏」管理 | 全站侧边栏渲染（带片段缓存，保存时触发缓存清理）|
| blog_blogsettings（博客全局配置）| 全站唯一配置：站名、SEO、摘要长度、评论开关、配色等 | 表：id bigint；site_name varchar(200)；site_description / site_seo_description / site_keywords longtext；article_sub_length int；sidebar_article_count / sidebar_comment_count / article_comment_count int；show_google_adsense bool；google_adsense_codes longtext；open_site_comment bool；comment_need_review bool；beian_code varchar(2000)；analytics_code longtext；show_gongan_code bool；gongan_beiancode / global_header / global_footer longtext；color_scheme varchar(20)〔8 套配色〕 | 后台「博客全局配置」（clean 约束全库仅一行；保存后清空缓存）；无记录时首次读取自动创建默认配置 | 全站页面（站名/SEO/配色/页头页脚/备案号）；评论分页数量与审核开关；摘要长度 |
| accounts_bloguser（用户）| 站点用户，扩展自 Django AbstractUser | 表：id bigint；username varchar(150) 唯一；password varchar(128)（哈希）；email varchar(254)；nickname varchar(100)；source varchar(100)；is_active / is_staff / is_superuser bool；last_login / date_joined datetime；first_name / last_name varchar(150)；creation_time / last_modify_time datetime | 注册页（source=Register，邮箱验证后激活）；OAuth 登录与绑定邮箱自动创建（source=authorize / emailconfirm）；后台用户管理；找回密码更新口令 | 登录认证（账号登录与 OAuth 绑定）；文章作者/评论作者关联展示；作者页；后台权限体系 |
| accounts_bloguser_groups（用户-用户组关联）| 用户与权限组的多对多中间表 | 表：id bigint；bloguser_id → accounts_bloguser；group_id → auth_group；UNIQUE(bloguser_id, group_id) | Django auth 权限体系（后台为用户分配组，ORM 自动维护）| 权限校验（组权限继承）|
| accounts_bloguser_user_permissions（用户-权限关联）| 用户与权限的多对多中间表 | 表：id bigint；bloguser_id → accounts_bloguser；permission_id → auth_permission；UNIQUE(bloguser_id, permission_id) | Django auth 权限体系（后台直接为用户授权，ORM 自动维护）| 权限校验（用户直授权限）|
| comments_comment（评论）| 文章评论，支持楼中楼回复与审核开关 | 表：id bigint；body longtext（限 300 字）；is_enable bool（审核通过才展示）；article_id → blog_article；author_id → accounts_bloguser；parent_comment_id → comments_comment（自关联，可空=顶层评论）；creation_time / last_modify_time datetime；组合索引（article, parent_comment, is_enable 等）| 文章详情页评论表单（登录用户提交；站点配置 comment_need_review=False 时直接启用，否则待后台审核）；后台评论管理 | 文章详情评论区（分页展示，带缓存）；侧边栏最新评论；回复邮件通知；缓存失效与搜索引擎推送逻辑 |
| comments_commentreaction（评论表情反应）| 用户对评论的 Emoji 反应（点赞）| 表：id bigint；reaction_type varchar(10)〔👍/👎/❤️/😄/🎉/😕/🚀/👀 共 8 种〕；created_at datetime；comment_id → comments_comment；user_id → accounts_bloguser；UNIQUE(comment_id, user_id, reaction_type) | 评论 Emoji 接口（登录用户点击，存在则删除取消、不存在则创建）| 评论区 reactions 统计展示（各表情数量与表态用户）|
| oauth_oauthuser（第三方授权用户）| 第三方平台登录用户信息，与本地用户可选绑定 | 表：id bigint；openid varchar(50)（平台内唯一标识）；nickname varchar(50)；token varchar(150)（访问令牌，可空）；picture varchar(350)（头像，可空）；type varchar(50)〔github/weibo/qq 等〕；email varchar(50)（可空）；metadata longtext（原始信息）；author_id → accounts_bloguser（可空，未绑定为空）；creation_time / last_modify_time datetime | OAuth 回调（授权成功后创建/更新第三方资料）；绑定邮箱页补充 email | 与本地用户绑定登录；头像本地化信号处理；后台管理 |
| oauth_oauthconfig（第三方登录配置）| 各第三方平台的接入配置 | 表：id bigint；type varchar(10)〔weibo/google/github/facebook/qq，clean 约束每平台仅一条〕；appkey varchar(200)；appsecret varchar(200)；callback_url varchar(200)；is_enable bool；creation_time / last_modify_time datetime | 后台「oauth配置」管理 | OAuth 管理器生成授权 URL；登录页第三方登录入口渲染（is_enable 过滤）|
| servermanager_commands（运维命令）| 微信机器人可远程执行的预定义命令 | 表：id bigint；title varchar(300)（命令标题）；command varchar(2000)（实际 shell 命令）；describe varchar(300)（描述）；creation_time / last_modify_time datetime | 后台「命令」管理（见 UC-SM-4）| 微信机器人 CommandHandler：helpme 帮助清单与管理员命令执行（按标题匹配）|
| servermanager_emailsendlog（邮件发送日志）| 每次邮件发送的记录与结果 | 表：id bigint；emailto varchar(300)；title varchar(2000)；content longtext；send_result bool；creation_time datetime | 邮件信号处理器在每次发送后自动写入（由注册验证、OAuth 绑定、评论通知等流程触发）| 后台「邮件发送log」只读查看（禁止手动新增）|

**（二）Django 内置支撑表（8 张，完整列出）**

| 数据条目 | 含义 | 类型/格式 | 来源 | 去向 |
|----------|------|-----------|------|------|
| auth_group（用户组）| 权限组定义 | 表：id int 主键；name varchar(150) 唯一 | 后台「组」管理创建 | 用户组分配（accounts_bloguser_groups）与组权限校验 |
| auth_group_permissions（组-权限关联）| 用户组与权限的多对多中间表 | 表：id bigint；group_id → auth_group；permission_id → auth_permission；UNIQUE(group_id, permission_id) | 后台给组配置权限（ORM 自动维护）| 权限校验（组权限继承）|
| auth_permission（权限项）| 系统全部权限条目 | 表：id int 主键；name varchar(255)；content_type_id → django_content_type；codename varchar(100)；UNIQUE(content_type_id, codename) | Django 迁移时按模型自动生成（增/删/改/查）| 用户/组授权界面勾选；权限校验 |
| django_admin_log（后台操作日志）| 后台上所有增删改操作的记录 | 表：id int 主键；action_time datetime；object_id longtext；object_repr varchar(200)；action_flag smallint unsigned（≥0，CHECK）；change_message longtext；content_type_id → django_content_type（可空）；user_id → accounts_bloguser | 后台操作时由 Django admin 自动记录 | 后台「操作历史」查看（LogEntryAdmin）|
| django_content_type（模型类型）| 每个模型的内容类型登记 | 表：id int 主键；app_label varchar(100)；model varchar(100)；UNIQUE(app_label, model) | Django 迁移时自动为每个模型生成 | auth_permission 关联；通用外键（如日志的对象类型）|
| django_migrations（迁移记录）| 数据库迁移的应用记录 | 表：id bigint；app varchar(255)；name varchar(255)；applied datetime | 每次执行 migrate 时写入 | 迁移状态判断（该迁移是否已应用）|
| django_session（会话）| 用户登录会话数据 | 表：session_key varchar(40) 主键；session_data longtext（编码后的会话内容）；expire_date datetime | 用户登录成功时写入（账号登录与 OAuth 登录均设置过期时间）| Django 会话中间件在每次请求时读取校验登录态；过期自动清理 |
| django_site（站点）| 站点域名信息（sites 框架）| 表：id int 主键；domain varchar(100) 唯一；name varchar(50) | 迁移初始数据（SITE_ID=1）；后台「站点」管理 | get_current_site 读取域名：拼接文章完整 URL、邮件链接、缓存键、CDN 清除 URL 等 |

## 2. 界面分析
> 负责人：黄梓涵 / 侍文博（开发经理）

（引入前面界面分析的结果，说明主要界面及其功能对应关系。）

---

## 3. 数据模型分析
> 负责人：朱亮宇（支持经理）

（引入前面数据模型分析的结果：类图、E-R 图、《软件数据模型设计说明书》。）

#### 【朱亮宇负责部分】数据模型分析

**3.1 建模依据与产物**

本节数据模型分析的原始产物均来自第四、五周实践，直接引入不重复建模：

| 产物 | 说明 | 出处 |
|------|------|------|
| 数据模型类图（StarUML 工程 + PNG 导出图）| 5 个 app 共 11 个模型类的 UML 类图，标注继承、关联与多重性 | 第四周《数据模型类图.puml / .png》，第六周按"统一用 StarUML 绘制"要求重绘并导出（工程文件 .uml + imgs/servermanager-plugins-classmodel-zly.png）|
| 数据模型类图分析 | 模型总览、核心字段说明、关系与多重性分析 | 第四周《数据模型类图分析.md》|
| 整体 E-R 图 | 全库实体-联系图（含实体、属性、1:1 / 1:N / N:M 联系）| 第五周《整体ER图-黄梓涵.png》|
| 《软件数据模型设计说明书》 | 逐表逐字段的中文说明、主外键关系、实体与 Model 对应汇总、约束与一致性说明 | 第五周《软件数据模型设计说明书（最终版）》（.md/.docx）|

**3.2 数据模型总体结构**

系统采用 Django ORM，把业务数据划分在 5 个 app 中，共 **11 个模型类**（另有抽象基类 BaseModel 不建表），与数据库 djangoblog 中的 16 张业务表对应：

| app | 模型类 | 数据库表 | 职责 |
|-----|--------|----------|------|
| accounts | BlogUser | accounts_bloguser | 博客用户（继承 Django AbstractUser）|
| blog | Article | blog_article | 文章 / 页面 |
| blog | Category | blog_category | 文章分类（支持父子树形）|
| blog | Tag | blog_tag | 文章标签 |
| blog | Links | blog_links | 友情链接 |
| blog | SideBar | blog_sidebar | 侧边栏自定义 HTML 块 |
| blog | BlogSettings | blog_blogsettings | 站点全局配置（单例）|
| comments | Comment | comments_comment | 文章评论（支持回复）|
| comments | CommentReaction | comments_commentreaction | 评论 Emoji 反应 |
| oauth | OAuthUser | oauth_oauthuser | 第三方登录用户 |
| oauth | OAuthConfig | oauth_oauthconfig | 第三方登录配置 |
| servermanager | commands | servermanager_commands | 运维命令 |
| servermanager | EmailSendLog | servermanager_emailsendlog | 邮件发送日志 |

> 另有 3 张由多对多字段自动生成的中间表：blog_article_tags、accounts_bloguser_groups、accounts_bloguser_user_permissions。

**3.3 数据模型类图（UML）**

![数据模型类图](imgs/servermanager-plugins-classmodel-zly.png)

> 图例：三角空心箭头表示继承（泛化）；实线箭头表示关联，两端标注多重性；`「」` 内为该字段的取值枚举。

**3.4 数据库整体 E-R 图**

![整体ER图](imgs/blog-er-hzh.png)

**3.5 模型关系与设计要点**

（1）**继承（泛化）关系**

| 子类 | 父类 | 说明 |
|------|------|------|
| BlogUser | AbstractUser（Django 内置）| 复用 Django 认证用户体系并扩展昵称、来源等字段 |
| Article / Category / Tag | BaseModel（抽象）| 复用主键与创建/修改时间字段，并在 save() 中自动生成 slug |

（2）**关联关系（含多重性）**

| 源 | 目标 | 关联字段 | 多重性 | 语义 |
|----|------|----------|--------|------|
| Article | Category | category | 1..* — 1 | 一个分类下有多篇文章，每篇文章必属一个分类 |
| Article | BlogUser | author | 1..* — 1 | 一个作者可写多篇文章 |
| Article | Tag | tags（M2M）| 1..* — 0..* | 文章与标签多对多 |
| Comment | Article | article | 0..* — 1 | 一篇文章可有多条评论 |
| Comment | BlogUser | author | 0..* — 1 | 一个用户可发多条评论 |
| CommentReaction | Comment | comment | 0..* — 1 | 一条评论可有多个表情反应 |
| CommentReaction | BlogUser | user | 0..* — 1 | 一个用户可对多条评论表态 |
| OAuthUser | BlogUser | author | 0..* — 0..1 | 第三方账号可选绑定一个本地用户 |

（3）**自关联（树形/楼中楼）**

- Category.parent_category（0..1 — 0..*）：构成"技术 → 后端开发/前端开发/数据库"式树形分类；
- Comment.parent_comment（0..1 — 0..*）：实现评论的楼中楼回复结构。

（4）**约束与一致性设计**

- 唯一约束：article.title、category.name、tag.name、bloguser.username、links.sequence、sidebar.sequence；
- 联合唯一：blog_article_tags(article_id, tag_id)、commentreaction(comment_id, user_id, reaction_type)、各权限中间表；
- CHECK 约束：article.views ≥ 0、django_admin_log.action_flag ≥ 0；
- 枚举取值受控：article.status/comment_status/type、commentreaction.reaction_type（8 种）、oauthconfig.type（5 平台）、blogsettings.color_scheme（8 配色）；
- 单例保护：BlogSettings.clean() 校验全库仅一行，save() 后清空缓存保证全站配置即时一致；
- 组合索引：article 按（type, status, pub_time）、（status, views）等四种场景建索引；comment 按（article, parent_comment, is_enable）等建索引，服务列表页与详情页查询。

（5）**与设计文档的衔接**：以上关系与约束的逐字段说明见第五周《软件数据模型设计说明书（最终版）》第 3 章；本文第 1.2 节数据字典与本章互为补充（前者面向"数据条目-流转"，后者面向"模型-关系"）。

## 4. 开源软件的软件架构及各个包和类的作用
> 负责人：各 app 负责人写自己 app 的包/类说明（blog=黄梓涵、accounts=侍文博、comments=刘雨婷、oauth=谢承志、servermanager/plugins=朱亮宇、djangoblog=张月）；整体架构图（UML 包图）=张月

分析软件中各个包的作用、每个包内的主要类和类的作用；绘制软件的架构图（采用 UML 包图绘制），标识包与架构的关系。

| 包 | 作用 | 包内主要类 | 类的作用 |
|----|------|-----------|----------|
| （如：blog）| | | |

#### 【朱亮宇负责部分】servermanager / plugins 包与类说明

| 包 | 作用 | 包内主要类 | 类的作用 |
|----|------|-----------|----------|
| servermanager | 服务器运维支持包：提供微信机器人（文章检索 / AI 问答 / 远程命令执行）、运维命令与邮件日志的管理、微信会话的缓存存储 | robot.py、api/blogapi.py、api/commonapi.py、MemcacheStorage、models、admin（详见下表）| 承载"服务器管理"相关的全部业务能力 |
| plugins | 插件扩展包：8 个可启停插件，通过钩子机制在文章内容、文章推荐、SEO、CDN 缓存等环节扩展系统功能 | 8 个插件主类 + CloudflareCacheHandler、CloudflareAPI（详见下表）| 以"钩子/信号"方式装配到主流程，不侵入核心业务代码 |

**（一）servermanager 包内主要类**

| 类 / 模块 | 类的作用 |
|-----------|----------|
| models.commands | 运维命令模型（标题/命令/描述/创建时间/修改时间），供机器人执行与帮助清单使用 |
| models.EmailSendLog | 邮件发送日志模型（收件人/标题/内容/发送结果/创建时间），按时间倒序 |
| admin.CommandsAdmin | 后台命令管理配置：列表展示标题、命令内容、描述 |
| admin.EmailSendLogAdmin | 后台邮件日志配置：只读展示，重写 has_add_permission 禁止手动新增 |
| api.blogapi.BlogApi | 博客数据查询封装：Haystack 搜索引擎检索（≤8 条）、全部分类、按分类查文章、最新文章；供机器人调用 |
| api.commonapi.ChatGPT | 静态工具类：调用 OpenAI gpt-3.5-turbo 完成对话，异常返回友好提示 |
| api.commonapi.CommandHandler | 命令处理器：加载 commands 表、按标题匹配命令、os.popen 执行 shell 并读取输出、拼接 helpme 帮助文本 |
| MemcacheStorage.MemcacheStorage | Werobot 会话存储类：get/set/delete 与可用性检测（is_available），key 加 ws_ 前缀，JSON 序列化会话 |
| robot（模块级实例）| WeRoBot 机器人实例：token 配置、会话支持、优先缓存/降级文件的存储选择 |
| robot.convert_to_article_reply | 把文章列表转换为微信图文消息（正则提取首图、标题、摘要、完整链接）|
| robot.search / category / recents / help / weather / idcard | 消息过滤器：?关键字搜索文章、分类目录、最新文章、帮助文本、天气与身份证（占位待开发）|
| robot.echo + MessageHandler | 默认消息处理器与业务处理类：管理员身份校验（双重 SHA256 密码、3 次锁定）、命令确认执行、AI 对话、会话信息维护 |
| robot.WxUserInfo | 微信用户会话实体：isAdmin / isPasswordSet / Count / Command 四个状态字段 |
| urls.py | 路由：用 make_view 暴露 /robot 微信消息回调接口 |

**（二）plugins 包内主要插件类**

| 插件（目录）| 主要类 | 注册钩子 | 类的作用 |
|-------------|--------|----------|----------|
| article_copyright | ArticleCopyrightPlugin | the_content | 正文末尾追加版权声明（摘要模式不添加）|
| reading_time | ReadingTimePlugin | the_content | 估算阅读时间插入正文顶部（约 200 字/分钟，最短 1 分钟，摘要模式跳过）|
| external_links | ExternalLinksPlugin | the_content | 外部链接自动加 target="_blank" 与 rel 安全属性，站内链接与已有 target 的链接跳过 |
| image_lazy_loading | ImageOptimizationPlugin | the_content | 图片懒加载、异步解码、响应式属性、alt 补全、首图 LCP 优化等 8 项处理 |
| view_count | ViewCountPlugin | after_article_body_get | 文章被访问后浏览量 +1（以 update_fields 限流，避免连带缓存清理）|
| seo_optimizer | SeoOptimizerPlugin | head_meta | 按页面类型动态生成 Open Graph 标签与 JSON-LD（文章/面包屑/站点三级）|
| article_recommendation | ArticleRecommendationPlugin | article_detail_load + 位置渲染 | 标签→分类→热门三级推荐策略，渲染文章底部"相关推荐"组件，含 CSS/JS 静态资源 |
| cloudflare_cache | CloudflareCachePlugin、CloudflareCacheHandler、CloudflareAPI | Article/Comment 的 post_save 信号 | 文章/评论保存后收集相关 URL 并分批精确清除 CDN 缓存；支持启动清理全站；凭证无效时自我禁用 |

> 说明：插件系统基座（BasePlugin、hooks 注册表、loader 加载器、hook 常量）位于 djangoblog 包（张月负责）；plugins 包中的插件通过继承 BasePlugin、实现 register_hooks 注册钩子回调接入系统，由 settings.ACTIVE_PLUGINS 控制启停。

（此处插入整体架构图——UML 包图，张月绘制）

## 5. 软件功能与类间的对应关系
> 负责人：各 app 负责人列自己 app 的对应关系；汇总总表=黄梓涵（开发经理）

（采用表格方式列出，表头参考如下：）

| 功能 | 对应类 | 所属包 | 说明 |
|------|--------|--------|------|

#### 【朱亮宇负责部分】servermanager / plugins 功能-类对应表

| 功能 | 对应类 | 所属包 | 说明 |
|------|--------|--------|------|
| 微信文章搜索（?关键字）| BlogApi.search_articles、robot.search | servermanager | Haystack 检索最多 8 条，组装图文消息回复 |
| 微信分类查询（category）| BlogApi.get_category_lists、robot.category | servermanager | 返回全部分类名列表 |
| 微信最新文章（recent）| BlogApi.get_recent_articles、robot.recents | servermanager | 取最新文章组装图文回复 |
| 微信帮助（help / helpme）| robot.help、CommandHandler.get_help | servermanager | 指令说明与运维命令清单 |
| 微信 AI 问答 | robot.echo、MessageHandler、ChatGPT | servermanager | 未匹配指令的消息交由 gpt-3.5-turbo 回复 |
| 管理员身份校验与远程命令执行 | MessageHandler、WxUserInfo、CommandHandler、MemcacheStorage | servermanager | 双重 SHA256 密码校验、命令确认、shell 执行、会话保存 |
| 运维命令维护 | commands、CommandsAdmin | servermanager | 后台增删改命令，机器人重启后生效 |
| 邮件发送日志 | EmailSendLog、EmailSendLogAdmin | servermanager | 信号处理器自动写入，后台只读查看 |
| 微信会话缓存 | MemcacheStorage | servermanager | 缓存优先、不可用时降级文件存储 |
| 机器人消息接入 | urls.py（make_view）| servermanager | /robot 微信回调路由 |
| 插件加载与启停 | loader.load_plugins、BasePlugin、hooks | djangoblog（基座）+ plugins（插件）| ACTIVE_PLUGINS 控制启用，重启加载 |
| 文章版权声明 | ArticleCopyrightPlugin | plugins | the_content 钩子追加版权信息 |
| 阅读时间估算 | ReadingTimePlugin | plugins | the_content 钩子插入预计阅读时间 |
| 外链安全处理 | ExternalLinksPlugin | plugins | the_content 钩子为外链加 target/rel |
| 图片性能优化 | ImageOptimizationPlugin | plugins | the_content 钩子为图片添加懒加载等属性 |
| 文章浏览量统计 | ViewCountPlugin | plugins | after_article_body_get 钩子触发 views+1 |
| SEO 元数据生成 | SeoOptimizerPlugin | plugins | head_meta 钩子生成 OG 与 JSON-LD |
| 相关文章推荐 | ArticleRecommendationPlugin | plugins | article_detail_load 钩子三级推荐策略 |
| CDN 缓存自动清除 | CloudflareCachePlugin、CloudflareCacheHandler、CloudflareAPI | plugins | post_save 信号触发按 URL 清除缓存 |

## 6. 总结
> 负责人：刘雨婷（计划经理）

（总结前一阶段小组协作的收获和问题，以及下一步改进的计划。）
