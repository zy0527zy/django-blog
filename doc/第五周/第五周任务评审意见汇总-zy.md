# 第五周任务评审意见汇总

## 朱亮宇 · servermanager 部分

- **评审人**：张月（组长）
- **评审对象**：`doc/第五周/软件数据模型设计说明书-servermanager部分.md`（分支 `zly_branch`，commit `7831e1b`）
- **核对依据**：`src/servermanager/models.py`、`src/servermanager/migrations/0001_initial.py` 与 `0002_alter_emailsendlog_options_and_more.py`、`doc/第五周/数据库表结构导出-朱亮宇.md`
- **评审结论**：✅ 整体合格，字段名 / 类型 / 长度 / 主键与源码及导出的表结构完全一致；发现 1 处需修正（model 类名大小写）+ 若干表述建议。

### 一、核对结果

| 表 | 核对项 | 结果 |
|---|---|---|
| servermanager_commands | 业务字段 5 个（title / command / describe / creation_time / last_modify_time）+ 自增主键 id | ✅ 字段名、类型、长度与源码 / 迁移 / 导出完全一致 |
| servermanager_commands | 类型 bigint / varchar(300) / varchar(2000) / datetime(6) | ✅ |
| servermanager_emailsendlog | 业务字段 5 个（emailto / title / content / send_result / creation_time）+ 自增主键 id | ✅ 一致 |
| servermanager_emailsendlog | 类型 varchar / longtext / tinyint(1) / datetime(6) | ✅ |
| 两张表 | 外键 | ✅ 均无外键，为独立工具表（无跨 app 关联）|

### 二、需修正的问题

#### 1.【错误】model 类名大小写：`Commands` → `commands`
- 文档在「3.2.5 表清单」「小节标题」「model 对应」多处写作 `Commands`，但源码实际类名为 `commands`（全小写，见 `models.py` 中 `class commands`）。
- 该错误源自模板 `软件数据模型设计说明书模板-张月.md` 的 3.2.5 行（模板即写 `Commands`），朱亮宇沿用了模板写法。
- **建议**：整合定稿时模板与正文统一改为 `commands`。若团队认为代码里 `commands` 命名不规范（代码库其它 model 均为 CamelCase），应先由开发经理统一在代码层改名，再同步文档，二者保持严格一致。

### 三、建议（不阻塞，可提升质量）

2. **`creation_time` / `last_modify_time` 建议注明自动维护语义**：二者分别由 Django `auto_now_add` / `auto_now` 自动维护（创建时 / 每次保存时自动写入），数据模型说明里体现这一点更能说明设计意图。

3. **`send_result` 说明可更明确**：类型 `tinyint(1)` 实为 `BooleanField`，建议注明「布尔值 0/1，默认 False」。

4. **`EmailSendLog`「仅可读，不允许新增」建议精确化**：该限制是 Django 后台（admin）层约束——`admin.py` 中 `readonly_fields` + `has_add_permission=False`，并非 model 层禁止写入；系统发邮件时仍会向该表写入日志。建议表述改为「后台只读、禁止手动新增；由系统邮件发送流程自动记录」。

5. **`commands.title` 说明与代码 verbose_name 不一致**：文档写「命令名称」，代码 `verbose_name='命令标题'`，建议统一。

6. **无外键可显式注明**：本部分两表均无外键关系，建议在 3.2.5 下显式注明「与其它实体无关联、无关系重数」，避免评审时被认为遗漏了「关系重数」这一项。

### 四、结论

除第 1 条（model 类名大小写）需在整合定稿时修正外，其余为表述优化建议，不阻塞合并。servermanager 部分字段类型、长度、主键、自增均准确，格式符合模板要求（①表结构表 + ②model 对应）。

---

## 刘雨婷 · comments 部分

- **评审人**：张月（组长）
- **评审对象**：`doc/第五周/软件数据模型设计说明书-comments部分-刘雨婷.md`（分支 `lyt_branch`，commit `406e39b`）
- **核对依据**：`src/comments/models.py`、`src/comments/views.py`、`doc/第五周/数据库表结构导出（最终版）.md`
- **评审结论**：✅ 整体合格，字段名 / 类型 / 长度 / 主键 / 索引 / 唯一约束与源码及导出的表结构完全一致，且正确区分了 `article_id`(int) 与 `author_id`(bigint)；发现 1 处需修正（跨 app 外键列举有误）+ 若干表述建议。

### 一、核对结果

| 表 | 核对项 | 结果 |
|---|---|---|
| comments_comment | 8 字段：id / body / creation_time / last_modify_time / author_id / article_id / parent_comment_id / is_enable | ✅ 字段名、类型与导出完全一致 |
| comments_comment | 类型 bigint / longtext / datetime(6) / int / tinyint(1) | ✅ |
| comments_comment | 外键 3 条：author→accounts_bloguser、article→blog_article、parent_comment→自身（可空） | ✅ 方向、目标、可空性均正确 |
| comments_comment | 索引 idx_art_parent_enable、idx_enable_id | ✅ |
| comments_commentreaction | 5 字段：id / comment_id / user_id / reaction_type / created_at | ✅ |
| comments_commentreaction | 类型 bigint / varchar(10) / datetime(6)；reaction_type 共 8 种 Emoji | ✅ |
| comments_commentreaction | unique_together(comment, user, reaction_type) + 索引 idx_comment_reaction | ✅ |

### 二、需修正的问题

#### 1.【错误】「与整体系统的关系」中跨 app 外键第 3 条写错：`reaction→comment` 应为 `reaction→user`
- 文档写「跨 app 外键共 3 条：comment→article、comment→author、reaction→comment」。
- 但 `reaction→comment` 是 comments app **内部**关联（reaction 表 → comment 表，同为 comments），不算跨 app。
- 真正的第 3 条跨 app 外键是 **`reaction→user`**（`comments_commentreaction.user_id` → `accounts_bloguser.id`）。
- 同一小节上一句也只列了 comment 表外键，漏掉了 reaction 表的 `comment_id`、`user_id`。
- **影响**：该节「供 E-R 图使用」，照抄会把整体 E-R 图（黄梓涵负责）画错。
- **建议**：整合定稿时改为——跨 app 外键共 3 条 = comment→article、comment→author、reaction→user。

### 三、建议（不阻塞，可提升质量）

2. `body` 的「上限 300 字」是应用层校验（`max_length=300`），数据库层 `longtext` 无长度限制，建议注明。
3. `is_enable` 按源码 `default=False` 写「默认 False=隐藏（待审核），审核通过置 True 后展示」更贴切。

### 四、结论

除第 1 条（`reaction→comment` 应为 `reaction→user`）需在整合定稿时修正外，其余为表述优化建议，不阻塞合并。

---

## 刘雨婷 · 任务跟踪表

- **评审人**：张月（组长）
- **评审对象**：`doc/第五周/任务跟踪表-刘雨婷.md`（分支 `lyt_branch`，commit `46bd894`）
- **结论**：✅ 合格——你填了截止时间、各成员状态，还新增「进度记录」小节，符合计划经理职责。
- **1 处建议更新**：朱亮宇的 servermanager 说明书已合并 develop（commit 2c035ac），「servermanager 表结构待确认」可改成「已完成」。

### 目前进度（张月同步）

- 张月：组会纪要、系统概述已 push；已评审朱亮宇 servermanager、刘雨婷 comments 两节。
- 朱亮宇：表结构导出最终版 + servermanager 说明书，均已合并 develop。
- 刘雨婷：comments 标注 + 表结构说明书 + 跟踪表，均已完成（待合并 develop）。
- 黄梓涵 / 侍文博 / 谢承志：待群内汇报。

### 注意事项

1. 跟踪表继续像现在一样持续更新各成员状态；
2. 有不清楚的进度，继续 push 任务跟踪表，我用 PR 回复你；
3. 本周作业结束时需提交一份「完整版」（整合本周次的完整文档），有不清楚的地方直接来问我。
