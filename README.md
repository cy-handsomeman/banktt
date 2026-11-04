# banktt 银行后台管理系统

基于 Django + Django REST Framework 的银行后台管理系统，提供客户信息、银行卡、交易流水，以及系统用户 / 角色 / 菜单 / 授权的管理与接口。

## 技术栈

| 组件 | 版本 | 用途 |
| --- | --- | --- |
| Python | 3.10+（实测 3.12） | 运行环境 |
| Django | 5.1.2 | Web 框架 |
| Django REST Framework | 3.15.2 | RESTful 接口 |
| djangorestframework-simplejwt | 5.3.1 | JWT 认证 |
| drf-spectacular | 0.29.0 | OpenAPI / Swagger 文档 |
| django-filter | 25.1 | 接口过滤 |
| MySQL | 8.0 | 数据库（InnoDB / utf8mb4） |
| mysqlclient | 2.2.5 | MySQL 驱动 |

## 目录结构

```
banktt/
├── manage.py                 # 项目入口
├── requirements.txt          # 依赖清单
├── .env.example              # 环境变量模板（可提交）
├── .env                      # 本地真实配置（禁止提交，已在 .gitignore 中）
├── sql/
│   └── bank_init.sql         # ★ 数据库初始化脚本（建库 + 8 张业务表 + 登录日志表 + 初始角色/菜单/管理员）
├── banktt/                   # 全局配置（settings.py / urls.py / wsgi.py / asgi.py）
├── apps/                     # 8 个业务应用
│   ├── sys_user/             # 系统用户
│   ├── sys_role/             # 系统角色
│   ├── sys_menu/             # 系统菜单
│   ├── sys_user_role/        # 用户-角色关联
│   ├── sys_role_menu/        # 角色-菜单关联
│   ├── user_info/            # 客户信息
│   ├── card_info/            # 银行卡信息
│   └── trade_info/           # 交易流水
├── static/                   # css / js 静态资源
└── templates/                # 页面模板（index.html / login.html）
```

## 环境要求

- **Python 3.10 及以上**（推荐 3.12）
- **MySQL 8.0**（需要 InnoDB 引擎与 utf8mb4 字符集）
- Windows / macOS / Linux 均可
- 无需 Redis、无需 Docker

## 快速开始

### 第 1 步：准备数据库

项目使用 8 张业务表 + 1 张登录日志表。模型已托管（`managed = True`）并生成初始迁移：可以用 `sql/bank_init.sql` 初始化数据库与种子数据，也可以用 `python manage.py migrate` 建表。

**方式 A：命令行（推荐）**

```bash
mysql -u root -p < sql/bank_init.sql
```

**方式 B：图形化工具（Navicat / DBeaver / MySQL Workbench）**

1. 新建连接，登录 MySQL 8.0
2. 右键连接 → 「运行 SQL 文件」→ 选择 `sql/bank_init.sql`
3. 执行完成后刷新，能看到 `bank` 库

**验证：**

```sql
USE bank;
SHOW TABLES;
```

应看到 9 张表：`sys_user`、`sys_role`、`sys_menu`、`sys_user_role`、`sys_role_menu`、`sys_login_log`、`user_info`、`card_info`、`trade_info`。

脚本同时写入初始数据：3 个角色、8 个菜单、角色菜单绑定，以及一个初始管理员账号。

**默认账号：`admin` / `admin123`**（密码在库中以 PBKDF2 哈希保存，登录后请立即修改）。

> 脚本使用 `CREATE TABLE IF NOT EXISTS` + `INSERT IGNORE`，可重复执行，不会清空已有数据。
>
> 如果已经用本脚本创建过表，首次还需执行 `python manage.py migrate --fake-initial`，把初始迁移登记为「已应用」（不会改动已有表结构）。

### 第 2 步：配置环境变量

复制模板并修改为真实值：

```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

然后编辑根目录的 `.env`：

| 变量 | 说明 | 示例 |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | 项目密钥，**必须自己生成一份新的** | 见下方命令 |
| `DJANGO_DEBUG` | 调试模式，本地开发填 `True` | `True` |
| `DJANGO_ALLOWED_HOSTS` | 允许访问的域名/IP，逗号分隔 | `127.0.0.1,localhost` |
| `DB_NAME` | 数据库名，与脚本一致 | `bank` |
| `DB_USER` | 数据库账号 | `root` |
| `DB_PASSWORD` | 数据库密码 | `12345678` |
| `DB_HOST` | 数据库地址 | `127.0.0.1` |
| `DB_PORT` | 数据库端口 | `3306` |

生成一个新的 `SECRET_KEY`：

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

> `.env` 已被 `.gitignore` 忽略，**不要提交到仓库**；`.env.example` 只放占位符，可以提交。

### 第 3 步：安装依赖

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境（Windows PowerShell）
.venv\Scripts\Activate.ps1

# 激活虚拟环境（macOS / Linux）
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

> 如果 PowerShell 提示「无法加载文件 Activate.ps1，因为在此系统上禁止运行脚本」，可跳过激活，直接用虚拟环境里的 Python 全路径执行命令：
>
> ```powershell
> .venv\Scripts\python.exe manage.py runserver
> ```

### 第 4 步：启动项目

```bash
python manage.py check          # 配置自检，应输出 "no issues"
python manage.py migrate        # 应用迁移（用 SQL 脚本建过表的旧库请加 --fake-initial）
python manage.py seed           # 可选：为缺少菜单的角色补齐全部菜单、给无角色用户分配默认角色（可重复执行）
python manage.py hash_passwords # 仅升级历史明文密码时使用，可加 --dry-run 预演
python manage.py runserver      # 启动开发服务器
```

看到下面的输出即启动成功：

```
System check identified no issues (0 silenced).
Django version 5.1.2, using settings 'banktt.settings'
Starting development server at http://127.0.0.1:8000/
```

### 第 5 步：访问页面

| 地址 | 内容 |
| --- | --- |
| http://127.0.0.1:8000/ | 首页（`index.html`） |
| http://127.0.0.1:8000/login/ | 登录页 |
| http://127.0.0.1:8000/menu/ | 菜单管理（仅超级管理员） |
| http://127.0.0.1:8000/login_log/ | 登录日志（仅超级管理员） |
| http://127.0.0.1:8000/docs/ | Swagger 接口文档 |
| http://127.0.0.1:8000/api/schema/ | OpenAPI 描述文件 |

接口统一前缀为 `/api/`，例如 `/api/user/`、`/api/card/`、`/api/trade/`、`/api/sys_user/`。

### 接口鉴权（JWT）

- 仅 `POST /api/sys_user/login/`、`/docs/`、`/api/schema/` 免登录；
- 其余 `/api/` 接口必须携带请求头：`Authorization: Bearer <access>`，否则返回 `401`；
- access 默认 60 分钟过期，前端 `auth.js` 会在 401 时自动用 refresh 换新 token 并重放请求；也可手动调用 `POST /api/token/refresh/`（body 传 `refresh`）换取新的 access；
- 退出登录会清空整个 `sessionStorage`（access / refresh / 用户名 / 用户ID）；
- 登录返回 `code / message / data`，`data` 中包含 `access`、`refresh`；
- `sys_user`、`sys_role`、`sys_menu`、`sys_role_menu`、`sys_user_role`、`login_log` 的访问仅超级管理员（`role_id=1`）。

## 数据库说明（重要）

- 8 个业务模型与登录日志模型均为 `managed = True`，表结构由 Django 迁移管理；
- 各应用的 `migrations/0001_initial.py` 已纳入版本管理，可用于建表与结构演进；
- `sql/bank_init.sql` 仍保留，用于初始化数据库与种子数据（`CREATE TABLE IF NOT EXISTS`，可重复执行）。

因此：

1. **旧库/本机已有表**：执行 `python manage.py migrate --fake-initial` 登记迁移，不会重建或改动表；
2. **全新环境**：先创建 `bank` 数据库，执行 `python manage.py migrate` 建表，再按需导入 `sql/bank_init.sql` 的种子数据；也可以先导入 SQL，再执行 `migrate --fake-initial`；
3. 需要调整表结构时：修改 `models.py` → `makemigrations` → `migrate`，并同步更新 `sql/bank_init.sql`。

运行单元测试（测试库由迁移自动建表）：`python manage.py test`。

## 常见问题

| 报错 | 原因 | 解决 |
| --- | --- | --- |
| `Can't connect to MySQL server (2003)` | MySQL 服务未启动 | 启动服务：`net start MySQL80` |
| `Access denied for user 'root' (1045)` | `.env` 中 `DB_PASSWORD` 不对 | 核对并修改 `.env` |
| `Unknown database 'bank' (1049)` | 未执行初始化脚本 | 执行第 1 步，导入 `sql/bank_init.sql` |
| `Table 'bank.sys_user' doesn't exist (1146)` | 表未创建 | 同上，导入 SQL 后重启服务 |
| `That port is already in use` | 8000 端口被占用 | `python manage.py runserver 8001` |
| `ModuleNotFoundError: No module named 'MySQLdb'` | 用的不是项目虚拟环境的 Python | 用 `.venv\Scripts\python.exe` 执行 |

## 生产部署要点

1. `.env` 中设置 `DJANGO_DEBUG=False`、真实的 `DJANGO_ALLOWED_HOSTS` 与 `DJANGO_SECRET_KEY`（缺少密钥会直接启动失败，避免误用开发默认值）。
2. 执行 `python manage.py collectstatic`，静态文件输出到 `staticfiles/`，由 Nginx 等 Web 服务器提供；`static/` 与 `media/` 已加入 `.gitignore`。
3. `media/` 目录同样交给 Web 服务器提供（Django 仅在 `DEBUG=True` 时代理该目录）。
4. 使用 Gunicorn / uWSGI 等 WSGI 服务启动，不要用 `runserver` 对外提供服务，并在前置代理上开启 HTTPS。

## 安全提醒

当前安全措施：

- 密码使用 Django 哈希（PBKDF2）存储，登录用 `check_password` 校验，并接入密码强度校验器；
- 全局默认权限 `IsAuthenticated`，登录与接口文档白名单放行；
- 系统用户 / 角色 / 菜单 / 授权接口（含查询）仅超级管理员可访问；
- 业务数据（客户 / 银行卡 / 交易）：登录即可查询，新增与修改要求已分配角色，删除仅超级管理员或大堂经理；
- 转账为双边记账：一次转账生成「转账转出」和「转账转入」两条流水，并同时更新两张卡的余额，两条流水不支持单独修改或删除；
- 银行卡有「正常 / 挂失 / 销户」三种状态：挂失与销户卡禁止发起任何交易；销卡仅超级管理员或大堂经理可办理，且要求卡内余额为 0；
- 交易支持冲正：由超级管理员或大堂经理发起，生成反向流水并把原交易标记为「已冲正」，转账会成对冲正；已冲正交易不可再修改或删除；
- 每笔交易记录 `balance_after`（交易后余额快照），交易日期由后端生成，客户端不可伪造；
- 登录成功与失败都会写入 `sys_login_log`（用户名、IP、浏览器标识、结果、时间），可在「登录日志」页面查询；
- 删除客户 / 银行卡 / 系统用户 / 角色前会先检查关联数据，被引用时返回 400 与中文原因，不再因外键约束报 500；
- 新建数据做格式校验：卡号 6-20 位数字、手机号 11 位、身份证 18 位；历史遗留数据保持原值时不拦截；
- 登录与全站接口均有限流（匿名 30 次/分钟、登录用户 300 次/分钟）。

关于银行卡密码与模型外键的说明：

- **银行卡密码仅登记不校验**：开户时密码以 PBKDF2 哈希入库，但当前交易接口不要求输入卡密码，也不做密码比对。本项目定位是柜面后台管理，密码字段仅用于存储与展示控制；若需要真实校验，需在交易提交时增加 `card_password` 入参并调用 `check_password`。
- **模型侧未声明 ForeignKey**：MySQL 中 `card_info.customer_id`、`trade_info.card_id`、`sys_user_role`、`sys_role_menu` 已有真实外键；但 `models.py` 保持 `IntegerField / CharField`，以便接口仍然直接收发 `customer_id` / `card_id` 标量，不改变既有 API 契约。关联完整性由数据库外键与视图层校验共同保证。

投入真实使用前仍建议补充：

- 修改初始管理员密码，并按需收紧业务数据的查看范围（当前登录用户均可查看全量客户/交易数据）；
- 为 `sys_user`、`user_info` 的手机号/身份证等敏感字段增加脱敏展示或更细的字段权限；
- 生产环境配置 HTTPS、日志审计与定期备份。
