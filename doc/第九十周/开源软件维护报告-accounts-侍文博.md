# 开源软件维护报告：accounts（侍文博）

## 5. 开源软件的维护

| 序号 | 维护类别 | 名称 | 维护的细节描述 | 负责该维护的组员 |
|---|---|---|---|---|
| 1 | 新增功能 | 用户头像上传与个人资料编辑 | 扩展 `BlogUser` 的 `avatar` 与 `bio` 字段；新增仅登录用户可访问的个人资料页，可编辑昵称、简介并上传头像。头像仅接受 JPG/JPEG、PNG、GIF、WebP 扩展名且大小不超过 5 MB。资料保存后清理侧栏缓存。 | 侍文博 |
| 2 | 新增功能 | 已登录用户修改密码 | 新增登录保护的密码修改页，复用 Django `PasswordChangeForm` 校验旧密码、新密码一致性和项目密码策略；成功后更新会话认证哈希，使当前会话继续登录。 | 侍文博 |

## 6. 开源软件维护所产生的设计

`BlogUser` 继承 Django `AbstractUser` 并扩展头像与简介字段。`ProfileForm` 绑定当前 `BlogUser` 实例并校验头像；`ProfileView` 继承项目 `AuthenticatedFormView`，处理当前用户资料读写及缓存清理。`AccountPasswordChangeForm` 继承 Django `PasswordChangeForm`；`AccountPasswordChangeView` 继承 `AuthenticatedFormView`，将当前用户交给表单，并在保存成功后更新 session auth hash。accounts URL 将资料页和改密页映射到相应视图。

维护后类图以橙色标示扩展的 `BlogUser`，绿色标示新增表单和视图，灰色标示 Django 或项目已有基类。源工程：[`accounts-maintained-swb.uml`](StarUML工程-侍文博/accounts-maintained-swb.uml)；PNG：[`accounts-maintained-swb.png`](imgs/accounts-maintained-swb.png)。

## 7. 维护代码数量及其质量情况

代码量按小组统一口径由朱亮宇汇总后补充。维护逻辑使用 Django ModelForm、认证视图及内置改密表单；头像在表单层限制扩展名和文件大小，改密沿用 Django 密码策略并更新会话哈希。测试记录见 [`accounts-test-record.md`](accounts-test-record.md)。本地 `.venv` 为 Django 5.2.17；测试使用临时 SQLite 配置，因为本机默认 MySQL 凭据不可用。

## 8. 维护后的软件原型

个人资料页提供昵称、个人简介和头像文件输入项，提交后显示保存提示；修改密码页提供旧密码、新密码和确认输入项，成功后显示更新提示。按本次提交要求，未附界面截图。
