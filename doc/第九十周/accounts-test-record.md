# accounts 基本测试记录（侍文博）

- 日期：2026-11-11
- 环境：仓库 `.venv`，Django 5.2.17（`src/requirements.txt` 要求 5.2.17）
- 命令：`python manage.py test accounts --settings=djangoblog._local_test_settings --verbosity 0`
- 数据库：临时 SQLite 内存库。本机默认 MySQL 测试库连接以 root 凭据失败（1045），故用临时本地 settings 覆盖数据库、邮件后端和缓存。测试结束已移除临时 settings，未改项目默认配置。
- 结果：54 个 accounts 测试全部通过；Django system check 无问题。

| 用例 | 操作 | 预期 | 结果 |
|---|---|---|---|
| 资料页访问控制 | 未登录访问 `/account/profile/` | 重定向至登录 | 通过 |
| 资料和头像保存 | 登录后提交昵称、简介和 PNG 头像 | 保存资料并保存头像到 `accounts/avatars/` | 通过 |
| 旧密码校验 | 提交错误旧密码 | 拒绝修改，原密码有效 | 通过 |
| 新密码及会话保持 | 提交正确旧密码和合规新密码 | 新密码生效，当前客户端仍为登录状态 | 通过 |
| accounts 回归 | 执行整个 accounts 测试套件 | 全部用例通过 | 54/54 通过 |

头像夹具使用 Pillow 生成有效 1×1 PNG，确保由 `ImageField` 完整解析。
