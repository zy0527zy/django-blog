# 第五周数据模型文档校对与评审意见

> 评审人：谢承志（质量/过程经理）｜ 日期：2026-10-10
> 评审对象：`doc/第五周/软件数据模型设计说明书-oauth数据模型部分-zy.md`
> 核对依据：`src/oauth/models.py`、迁移文件 `0001_initial.py` / `0002_alter_oauthconfig_options_alter_oauthuser_options_and_more.py` / `0003_alter_oauthuser_nickname.py`、`doc/第五周/数据库表结构导出（最终版）.md`、《数据模型文档编写规范》
> 评审结论：✅ 合格，字段名 / 类型 / 长度 / 主外键与源码及导出表结构一致，关系重数标注正确。

---

## 一、核对结果

| 表 | 核对项 | 结果 |
|---|---|---|
| oauth_oauthuser | 业务字段 10 个（openid / nickname / token / picture / type / email / metadata / author_id / creation_time / last_modify_time）+ 自增主键 id | ✅ 字段名、类型、长度与源码 / 迁移 / 导出完全一致 |
| oauth_oauthuser | 类型 bigint / varchar(50) / varchar(150) / varchar(350) / longtext / datetime(6) | ✅ |
| oauth_oauthuser | 外键 author_id → accounts_bloguser.id（可空，`null=True`） | ✅ 与 `0001_initial.py` 约束一致 |
| oauth_oauthconfig | 业务字段 6 个（type / appkey / appsecret / callback_url / is_enable / creation_time / last_modify_time）+ 自增主键 id | ✅ 一致 |
| oauth_oauthconfig | 类型 varchar(10) / varchar(200) / tinyint(1) / datetime(6) | ✅ |
| oauth_oauthconfig | 外键 | ✅ 无外键，独立配置表（无跨 app 关联） |

## 二、关系重数核对

| 关系 | 文档标注 | 核对结果 |
|---|---|---|
| oauth_oauthuser.author → accounts_bloguser | 0..1 : 1（可选绑定） | ✅ 与模板 3.1 节「第三方账号绑定（0..1:1）」一致；`author` 为 `null=True, blank=True` 的外键，可选绑定语义正确 |

## 三、符合编写规范的情况

1. 文件命名、引言四行、分节编号 `3.2.4` ✅ 符合规范；
2. 表结构表五列（字段/类型/主键/外键/说明）与分隔行 ✅ 符合规范；
3. `model 对应` 采用「数据 / 职责 / 关系重数」三段式 ✅ 符合规范；
4. `BooleanField` 注明「布尔 0/1，默认 True」、`default=now` 注明自动写入语义 ✅ 符合规范；
5. 3.3 汇总表补充了 oauth 两行 ✅ 便于组长整合。

## 四、遗留提示（不阻塞）

- `OAuthConfig.type` 原默认值 `'a'` 不在 TYPE 枚举内，属上游代码历史遗留，本次已同步修正为 `default='github'`（纯 Python 层默认值，无需迁移）。
- `OAuthUser.type` 为 `varchar(50)` 自由文本，未加 choices 约束，实际取值与 OAuthConfig.TYPE 对应，已按源码如实标注。

---

> 说明：本意见由谢承志（质量/过程经理）职责产出，随 oauth 分节一并提交；待全组各 app 分节到齐后，再统一做最终校对与格式整合（配合张月）。
