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
│   └── bank_init.sql         # ★ 数据库初始化脚本（建库 + 8 张业务表）
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

项目使用 8 张业务表，其中 7 个模型标记为 `managed = False`（数据库优先），**Django 不会自动建表**，必须先导入 `sql/bank_init.sql`。

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

应看到 8 张表：`sys_user`、`sys_role`、`sys_menu`、`sys_user_role`、`sys_role_menu`、`user_info`、`card_info`、`trade_info`。

> 脚本使用 `CREATE TABLE IF NOT EXISTS`，可重复执行，不会清空已有数据。

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
| http://127.0.0.1:8000/docs/ | Swagger 接口文档 |
| http://127.0.0.1:8000/api/schema/ | OpenAPI 描述文件 |

接口统一前缀为 `/api/`，例如 `/api/user/`、`/api/card/`、`/api/trade/`、`/api/sys_user/`。

## 数据库说明（重要）

本项目采用**数据库优先（database-first）**设计：

- 除 `SysUser` 外，其余 7 个模型都是 `managed = False`，Django 不会对它们建表、改表或删表；
- 各应用的 `migrations/` 目录中只有 `__init__.py`，**没有任何迁移文件**；
- 表结构的唯一来源是 `sql/bank_init.sql` 与真实 MySQL 数据库。

因此：

1. **不要执行** `python manage.py makemigrations` 来改动这些业务表；
2. 需要调整表结构时，同时修改三处：MySQL 中的表 → 对应 `models.py` → `sql/bank_init.sql`；
3. 换新环境时，只执行第 1 步导入 SQL 即可，无需 `migrate`。

## 常见问题

| 报错 | 原因 | 解决 |
| --- | --- | --- |
| `Can't connect to MySQL server (2003)` | MySQL 服务未启动 | 启动服务：`net start MySQL80` |
| `Access denied for user 'root' (1045)` | `.env` 中 `DB_PASSWORD` 不对 | 核对并修改 `.env` |
| `Unknown database 'bank' (1049)` | 未执行初始化脚本 | 执行第 1 步，导入 `sql/bank_init.sql` |
| `Table 'bank.sys_user' doesn't exist (1146)` | 表未创建 | 同上，导入 SQL 后重启服务 |
| `That port is already in use` | 8000 端口被占用 | `python manage.py runserver 8001` |
| `ModuleNotFoundError: No module named 'MySQLdb'` | 用的不是项目虚拟环境的 Python | 用 `.venv\Scripts\python.exe` 执行 |

## 安全提醒

当前仓库为教学 / 课程项目，投入真实使用前至少需要完成：

- `DJANGO_DEBUG=False`，并把 `ALLOWED_HOSTS` 改为真实域名
- 使用新生成的 `SECRET_KEY`，不要沿用开发默认值
- 登录密码目前为明文比对，应改为哈希存储（`make_password` / `check_password`）
- 关闭全局 `AllowAny`，改为基于 JWT 的 `IsAuthenticated` 权限
