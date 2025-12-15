# 阶段进展（Phase Log）

## Phase 1：需求 + 后端骨架 + 数据库落库（已完成）
- 文档：`docs/SPEC.md`、`docs/ENV.md`
- 后端：Django + DRF + SimpleJWT 项目骨架（`backend/`）
  - 自定义用户：`accounts.User`（继承 `AbstractUser`，新增 `real_name/phone/created_at/updated_at`），已配置 `AUTH_USER_MODEL`
  - 业务 apps：`accounts`、`inventory`、`borrowing`、`maintenance`
  - 最小接口：`GET /api/v1/health/` → `{"status":"ok"}`
- 数据库：MySQL（`lab_manage`）
  - 13 张业务表已创建并与要求同名：`user`、`role`、`user_role`、`equipment`、`equipment_category`、`equipment_status_log`、`borrow_request`、`borrow_item`、`borrow_approval`、`return_record`、`maintenance`、`consumable`、`stock_txn`
  - 状态字段使用 `TextChoices`；业务表统一 `created_at/updated_at`

## 已验证（本地）
- `python manage.py makemigrations` / `python manage.py migrate`
- `python manage.py runserver` 可启动
- 健康检查可访问：`/api/v1/health/`
- `python manage.py createsuperuser` 可创建超级管理员

## Phase 2（建议下一步）
- 认证：接入 SimpleJWT 登录/刷新接口（或自定义登录视图）
- RBAC：基于 `role/user_role` 的权限模型与 `permission classes`
- 业务接口：设备台账、借用流程、耗材库存与预警、维修、统计报表
- 事务一致性：出库 `select_for_update + 状态校验`；耗材扣库存 `事务 + F 表达式/行锁` 防负库存
- 前端：路由/页面骨架、Axios 封装、Pinia 状态与权限路由守卫

## Phase 2.1：设备台账 API（已完成）
- 设备分类 CRUD：`/api/v1/equipment-categories/`
- 设备台账 CRUD：`/api/v1/equipment/`（支持 status/category/keyword 过滤 + 分页）
- 设备状态变更：POST `/api/v1/equipment/{id}/status/`（写状态日志）
- 设备状态日志：GET `/api/v1/equipment/{id}/logs/`
- 权限：管理员可写；老师/学生只读（`IsAdminOrReadOnly`）
