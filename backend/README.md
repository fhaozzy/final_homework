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

## 用户与角色 API（v1，仅管理员）
- 用户：`/api/v1/users/`（CRUD）
- 启用/停用：`PATCH /api/v1/users/{id}/activate/` / `PATCH /api/v1/users/{id}/deactivate/`
- 角色：`/api/v1/roles/`（CRUD）
- 用户角色：`/api/v1/user-roles/`（创建/删除）

## 常用命令
- 生成迁移：`python manage.py makemigrations`
- 执行迁移：`python manage.py migrate`
- 创建超级管理员：`python manage.py createsuperuser`（自动分配ADMIN角色）
- 本地运行：`python manage.py runserver 0.0.0.0:8000`

## 健康检查
- `GET /api/v1/health/` → `{"status": "ok"}`

## 当前用户（用于前端角色判定）
- `GET /api/v1/me/` → `{id, username, real_name, email, phone, roles, is_admin}`

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
- 列表/详情：`GET /api/v1/borrow/requests/`（管理员全量；老师全量只读；学生仅自己）/ `GET /api/v1/borrow/requests/{id}/`

## 维修 API（v1）
- 维修单：`/api/v1/maintenance/`（列表/创建/更新；写入需要管理员或 MAINTAINER 角色）

## 耗材与库存 API（v1）
- 耗材：`/api/v1/consumables/`（管理员可写，其余只读；字段含 `safety_stock/current_qty`）
- 预警：`GET /api/v1/consumables/warnings/`（`current_qty < safety_stock`）
- 入库：`POST /api/v1/stock/in/`（管理员；直接 APPROVED；增加库存）
- 领用申请：`POST /api/v1/stock/out/`（学生/老师；生成 OUT + PENDING；不扣库存）
- 审核：`POST /api/v1/stock/{id}/approve/` / `POST /api/v1/stock/{id}/reject/`（管理员；approve 使用事务 + 行锁/F 表达式防负库存）

### curl 示例（Windows PowerShell）
```bash
curl.exe -X POST http://127.0.0.1:8000/api/v1/auth/token/ -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"Admin123!\"}"
curl.exe -X POST http://127.0.0.1:8000/api/v1/consumables/ -H "Authorization: Bearer <ACCESS>" -H "Content-Type: application/json" -d "{\"code\":\"C-001\",\"name\":\"一次性手套\",\"unit\":\"盒\",\"category\":\"耗材\",\"safety_stock\":10,\"location\":\"A1\"}"
curl.exe -X POST http://127.0.0.1:8000/api/v1/stock/in/ -H "Authorization: Bearer <ACCESS>" -H "Content-Type: application/json" -d "{\"consumable_id\":1,\"qty\":50,\"remark\":\"采购\"}"
curl.exe -X POST http://127.0.0.1:8000/api/v1/stock/out/ -H "Authorization: Bearer <ACCESS>" -H "Content-Type: application/json" -d "{\"consumable_id\":1,\"qty\":8,\"remark\":\"实验\"}"
curl.exe -X POST http://127.0.0.1:8000/api/v1/stock/1/approve/ -H "Authorization: Bearer <ACCESS>"
curl.exe -X GET http://127.0.0.1:8000/api/v1/consumables/warnings/ -H "Authorization: Bearer <ACCESS>"
```

## 报表 API（v1，管理员/老师可读）
- 借用排行：`GET /api/v1/reports/borrow-top/?limit=10&start=YYYY-MM-DD&end=YYYY-MM-DD`
- 设备利用率：`GET /api/v1/reports/equipment-utilization/?start=YYYY-MM-DD&end=YYYY-MM-DD&include_zero=1`
- 耗材月消耗：`GET /api/v1/reports/consumable-monthly/?year=2025`

## 验收检查
- 确保已运行 `python manage.py migrate`（MySQL 连接正常）  
- 运行开发服务器：`python manage.py runserver`  
- 访问 `http://127.0.0.1:8000/api/v1/health/` 返回 `{"status":"ok"}`  
- 使用 `python manage.py createsuperuser` 可成功创建超级管理员账号

## 兼容提示
- 使用 mysqlclient 2.2.x；如需测试客户端请求，`DJANGO_ALLOWED_HOSTS` 可加入 `testserver`。
