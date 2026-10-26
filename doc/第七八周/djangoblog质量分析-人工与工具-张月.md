# djangoblog 代码质量分析（人工 + 工具）

> 负责人：张月（组长）· app：djangoblog（27 个 .py，约 1600 行）
> 分析工具：ruff 0.17.1 / flake8 7.4.1 / pylint 4.1.3（配置见仓库根目录 ruff.toml / .flake8，行宽 120）
> 本文件为报告第 3 节「人工分析」、第 4 节「工具分析」djangoblog 部分，及第 6 节「改进计划」素材。

---

## 一、工具分析情况（第 4 节）

### 1.1 方法与工具
- 单文件：VS Code 扩展（Ruff / Pylint）实时波浪线；
- 整包：命令行 `ruff check src/djangoblog`、`flake8 src/djangoblog`；
- 配置：仓库根目录 `ruff.toml` / `.flake8`（行宽 120，排除 venv / migrations / frontend 等）。

### 1.2 分析结果（修复前 → 修复后）

| 工具 | 修复前 | 修复后 | 已修复 |
|---|---:|---:|---:|
| Ruff | 224 | 152 | 72（`--fix` 自动）|
| Flake8 | 约 215 | 约 191 | 约 24 |

> 修复方式：`ruff check src/djangoblog --fix` 自动修复 72 处**安全项**（未用 import、import 排序、f-string、unicode 前缀、行尾空白、无效转义等），未使用 `--unsafe-fixes`（避免误删变量等风险操作）。

### 1.3 修复后剩余问题分类

| 规则 | 数量 | 含义 | 处理意见 |
|---|---:|---|---|
| F403 / F405 | 51 | `admin_site.py` 用 `from x import *` 星号导入，导致名字无法静态判定 | 属 Django admin 惯用写法，**待重构**（改显式导入），有风险先记录 |
| F841 | 35 | 局部变量赋值未使用 | 主要在 whoosh 后端 / 测试，**待清理** |
| E501 | 28 | 行过长（>120） | 需手动换行，**部分修** |
| E265 | 63 | 块注释应以 `# `（井号+空格）开头 | 由 `#zy:` 注释格式所致（任务要求 `#xxx:`），**预期项，不计** |
| UP031 | 19 | `%` 格式化可改 f-string | **待改** |
| C901 | 8 | 函数圈复杂度过高（12~34） | 集中在 whoosh 后端 vendored 代码，**待重构** |
| E722 | 1 | 裸 `except:` | 已人工定位（utils.py），**待收窄** |
| SIM / C417 / B007 / B904 | 各若干 | 可简化写法 | **待改** |

---

## 二、人工分析情况（第 3 节）

### 2.1 代码风格
- 整体遵循 PEP8，注释充分（前几周标注 + 本周 `#zy:` 精读标注覆盖全部 27 个文件）；
- 说明：`#zy:` 注释格式（任务要求）会触发 flake8 `E265`（# 后无空格），属**预期项**，不代表风格问题。

### 2.2 代码设计
**优点（遵循设计原则）**：
- 高内聚/低耦合：`mixins.py` 用职责单一的 Mixin 组合（时间戳 / 缓存 / 查询优化 / 分页）；
- 解耦：`blog_signals.py` 用「信号 + 副作用」分离业务与缓存清理/邮件/推送；
- 抽象：`elasticsearch_backend.py` / `whoosh_cn_backend.py` 双搜索后端同一接口；
- 可扩展：`plugin_manage/` 运行时动态加载插件系统（非标准 Django 能力）。

**问题**：
- `admin_site.py` 星号导入（F403/F405）——图省事但破坏可追踪性；
- `blog_signals.py` 用 `'get_full_url' in dir(instance)` 判断方法存在（应 `hasattr`）。

### 2.3 编程技能（亮点示例）
- `utils.sanitize_html()` 用 bleach 三级白名单（标签/属性/协议）防 XSS；
- `elasticsearch_backend.py` 兼容 ES 8.x `total` 由数字变对象（`isinstance` 判断）；
- `logentryadmin.py` 日志只读化 + `prefetch_related` 避免 N+1；
- `mixins.TimeStampedModel.save()` 自动维护 `updated_at`（含 `update_fields` 处理）。

### 2.4 代码质量问题（精读发现，共 8 处）

| # | 位置 | 问题 | 是否修复 |
|---|---|---|---|
| 1 | urls.py:45 | `handle403` 拼写错误，应为 `handler403`，自定义 403 页不生效 | 待修 |
| 2 | spider_notify.py | `notify(url)` 把单字符串传 `baidu_notify`，`'\n'.join` 逐字符拆开 | 待修 |
| 3 | sitemap.py | `list(set(map(...)))` 求作者去重，N+1 + 全量加载内存 | 待修 |
| 4 | sitemap.py | `changefreq="Weekly"` 大小写不合协议（应小写）| 待修 |
| 5 | feeds.py | `author_name` 的 `.first()` 无用户时 `None` → 抛异常 | 待修 |
| 6 | mixins.py | 缓存命中用 `if value:`，空结果误判未命中 | 待修 |
| 7 | blog_signals.py | `dir()` 判断方法存在，开销大（应 `hasattr`）| 待修 |
| 8 | utils.py | 裸 `except:`；`'jpeg'` 少点（应 `.jpeg`）| 待修 |

---

## 三、下一步改进计划（第 6 节素材）

结合上面人工 + 工具发现，下一步（第 9-10 周系统修改）优先改进：

| 优先级 | 改进点 | 现状 | 方案 |
|:---:|---|---|---|
| 高 | 修复 `handle403` 拼写 | 403 自定义页失效 | 改 `handler403` 并验证 |
| 高 | 修复 `spider_notify.notify` 传参 | 推送数据错乱 | 改传 `[url]` |
| 高 | 收窄 `utils.py` 裸 except | 吞异常 | 缩小为具体异常类型 |
| 中 | 清理 `admin_site.py` 星号导入 | 51 处 F403/F405 | 改显式导入 |
| 中 | 优化 `sitemap.py` 作者去重 | N+1 查询 | 数据库层 `distinct` |
| 中 | 清理未用变量（F841）| 35 处 | 手动删减 |
| 低 | `%` 格式化改 f-string | 19 处 | 逐处改 |
| 低 | 拆分 whoosh 后端高复杂度函数 | C901 8 处 | 逐函数重构 |
