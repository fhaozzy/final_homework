# 环境与运行说明

## 操作系统
- Microsoft Windows 10.0.26100.7171

## 运行时与工具版本
- Python 3.12.7
- Node.js v20.18.0
- npm 10.8.2
- MySQL 8.0.42 (MySQL Community Server)

## 虚拟环境建议（Windows PowerShell）
1. 创建：`python -m venv .venv`
2. 激活：`.\.venv\Scripts\activate`
3. 安装后端依赖：`cd backend && pip install -r requirements.txt`
4. 复制配置：`Copy-Item .env.example .env`（位于 `backend/` 下）并填写 MySQL 密码与密钥
5. 退出虚拟环境：`deactivate`

## 当前虚拟环境 (.venv) 状态
- 路径：`.venv`（Python 3.12.7，home=D:\anconda，include-system-site-packages=false）
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

## 后端启动与验收（backend/）
1. 迁移：`python manage.py migrate`
2. 创建管理员：`python manage.py createsuperuser`
3. 启动：`python manage.py runserver 0.0.0.0:8000`
4. 健康检查：`GET http://127.0.0.1:8000/api/v1/health/` → `{"status":"ok"}`

## 备注
- `.env` 已加入 `.gitignore`；请使用 `backend/.env.example` 作为模板。
- 如需在 Django Test Client 中请求，`DJANGO_ALLOWED_HOSTS` 可临时加入 `testserver`。
