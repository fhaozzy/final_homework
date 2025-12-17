# 环境与运行说明

## 操作系统
- Windows（PowerShell）

## 运行时与工具版本
- Python 3.12+
- Node.js 20+
- npm 10+
- MySQL 8.0+

## 虚拟环境建议（Windows PowerShell）
1. 创建：`python -m venv .venv`
2. 激活：`.\.venv\Scripts\activate`
3. 安装后端依赖：`cd backend && pip install -r requirements.txt`
4. 复制配置：`Copy-Item .env.example .env`（位于 `backend/` 下）并填写 MySQL 密码与密钥
5. 退出虚拟环境：`deactivate`

## 当前虚拟环境 (.venv) 状态
- 路径：`.venv`（建议使用 Python 3.12+；不依赖系统 Python 路径）
- 已安装包（.venv 内 pip freeze）：
  ```
  asgiref==3.11.0
  Django==6.0
  django-cors-headers==4.9.0
  djangorestframework==3.16.1
  djangorestframework_simplejwt==5.5.1
  pip==25.3
  PyJWT==2.10.1
  mysqlclient==2.2.4
  python-dotenv==1.2.1
  sqlparse==0.5.4
  tzdata==2025.3
  ```

## 数据库准备
- 已创建本地数据库：`lab_manage`（utf8mb4）。如需重建：`mysql -u root -e "CREATE DATABASE IF NOT EXISTS lab_manage DEFAULT CHARACTER SET utf8mb4;"`

## 前后端联调验收（按演示脚本走）
> 目标：从登录开始，串起设备台账、借用流程、耗材库存、维修、报表、管理后台。

### 1) 准备
1. 确保 MySQL 已启动，且存在库 `lab_manage`（或 `backend/.env` 中 `MYSQL_DATABASE` 指定的库）。
2. 配置后端环境变量：复制 `backend/.env.example` 为 `backend/.env`，并填写 `DJANGO_SECRET_KEY` 与 `MYSQL_*`。
3. 配置前端环境变量：复制 `frontend/.env.example` 为 `frontend/.env`（一般保持 `VITE_API_BASE_URL=/api/v1`）。

### 2) 启动后端（PowerShell 窗口 1）
1. `cd <project_root>`（项目根目录，包含 `backend/`、`frontend/`、`.venv/`）
2. `.\.venv\Scripts\Activate.ps1`
3. `cd backend`
4. `pip install -r requirements.txt`
5. `python manage.py migrate`
6. `python manage.py createsuperuser`
7. `python manage.py runserver 0.0.0.0:8000`
8. 验证：访问 `http://127.0.0.1:8000/api/v1/health/` 返回 `{"status":"ok"}`

### 3) 启动前端（PowerShell 窗口 2）
1. `cd <project_root>\frontend`（或先 `cd <project_root>` 再 `cd frontend`）
2. `npm i`
3. `npm run dev`
4. 打开 `http://127.0.0.1:5173/`

### 4) 全流程验收（前端 UI）
按 `frontend/README.md` 的「演示脚本（前端全流程）」从 0 → 6 逐步操作即可，关键验收点：
- 学生：只看自己的借用单；访问报表路由会被拦截并提示“无权限”；库存流水仅本人。
- 老师：可看全量借用单但无法操作审批/出库/归还；可访问 3 个报表页。
- 管理员：可跑通借用全流程；耗材库存不足时 approve 提示失败；可维护用户/角色。
- 维修员：可创建维修单并推进 `OPEN→IN_PROGRESS→DONE`；DONE 后设备回 `AVAILABLE` 且状态日志更新。

## 备注
- `.env` 已加入 `.gitignore`；请使用 `backend/.env.example` 作为模板。
- 如需在 Django Test Client 中请求，`DJANGO_ALLOWED_HOSTS` 可临时加入 `testserver`。
