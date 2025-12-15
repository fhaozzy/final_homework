# 后端启动指引

## 环境
- 使用虚拟环境：`.\.venv\Scripts\activate`
- 安装依赖：`pip install -r requirements.txt`
- 复制配置：`Copy-Item .env.example .env` 并填写 MySQL 与密钥

## 关键配置
- 自定义用户：`AUTH_USER_MODEL = "accounts.User"`，字段包含 `real_name`、`phone`、`created_at`、`updated_at`
- 数据库：MySQL，通过环境变量 `MYSQL_DATABASE / MYSQL_USER / MYSQL_PASSWORD / MYSQL_HOST / MYSQL_PORT` 配置
- 认证：DRF + SimpleJWT（Bearer Token）

## 数据表
- 13 张业务表使用 `db_table` 对齐命名要求：`user/role/user_role/equipment/.../stock_txn`（详见 `docs/SPEC.md`）

## 常用命令
- 生成迁移：`python manage.py makemigrations`
- 执行迁移：`python manage.py migrate`
- 创建超级管理员：`python manage.py createsuperuser`
- 本地运行：`python manage.py runserver 0.0.0.0:8000`

## 健康检查
- `GET /api/v1/health/` → `{"status": "ok"}`

## 设备台账 API（v1）
- JWT 获取 token：`POST /api/v1/auth/token/`
- 分类：`/api/v1/equipment-categories/`（管理员可写，其余只读）
- 设备：`/api/v1/equipment/`（管理员可写，其余只读；支持 `status/category/keyword` + 分页）
- 状态变更：`POST /api/v1/equipment/{id}/status/`（写 `equipment_status_log`）
- 状态日志：`GET /api/v1/equipment/{id}/logs/`

## 借用流程 API（v1）
- 申请：`POST /api/v1/borrow/requests/`（学生/老师）
- 审批：`POST /api/v1/borrow/requests/{id}/approve/` / `POST /api/v1/borrow/requests/{id}/reject/`（管理员）
- 出库：`POST /api/v1/borrow/requests/{id}/checkout/`（管理员；事务 + 行锁；仅 AVAILABLE）
- 归还验收：`POST /api/v1/borrow/requests/{id}/return/`（管理员）
- 列表/详情：`GET /api/v1/borrow/requests/`（管理员全量；普通用户仅自己）/ `GET /api/v1/borrow/requests/{id}/`

## 验收检查
- 确保已运行 `python manage.py migrate`（MySQL 连接正常）  
- 运行开发服务器：`python manage.py runserver`  
- 访问 `http://127.0.0.1:8000/api/v1/health/` 返回 `{"status":"ok"}`  
- 使用 `python manage.py createsuperuser` 可成功创建超级管理员账号

## 兼容提示
- 使用 mysqlclient 2.2.x；如需测试客户端请求，`DJANGO_ALLOWED_HOSTS` 可加入 `testserver`。
