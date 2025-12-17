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

## Phase 2：后端业务接口 + RBAC（已完成）
- 认证：SimpleJWT（`/api/v1/auth/token/`、`/api/v1/auth/token/refresh/`）
- RBAC：基于 `role/user_role` + DRF permission classes（ADMIN/TEACHER/MAINTAINER/STUDENT）
- 当前用户：`GET /api/v1/me/`（前端用于稳定角色菜单/路由守卫；返回 `roles` 与 `is_admin`）
- 事务一致性：
  - 出库：`transaction.atomic + select_for_update` 锁设备，仅 `AVAILABLE` 可出库
  - 耗材扣库存：`transaction.atomic` + 行锁/F 表达式，保证不为负库存

## Phase 2.1：设备台账 API（已完成）
- 设备分类 CRUD：`/api/v1/equipment-categories/`
- 设备台账 CRUD：`/api/v1/equipment/`（支持 status/category/keyword 过滤 + 分页）
- 设备状态变更：POST `/api/v1/equipment/{id}/status/`（写状态日志）
- 设备状态日志：GET `/api/v1/equipment/{id}/logs/`
- 权限：管理员可写；老师/学生只读（`IsAdminOrReadOnly`）

## Phase 2.2：借用流程 API（已完成）
- 申请：POST `/api/v1/borrow/requests/`（学生/老师）→ `REQUESTED`
- 审批：POST `/api/v1/borrow/requests/{id}/approve/` / `/reject/`（管理员）→ 写 `borrow_approval`
- 出库：POST `/api/v1/borrow/requests/{id}/checkout/`（管理员）→ 事务 + 行锁；设备 `AVAILABLE`→`BORROWED`；写 `equipment_status_log`；request→`OUT`
- 归还验收：POST `/api/v1/borrow/requests/{id}/return/`（管理员）→ 写 `return_record`；设备→`AVAILABLE`；写 `equipment_status_log`；request→`CLOSED`
- 列表/详情：GET `/api/v1/borrow/requests/`（管理员全量；老师全量只读；学生仅自己）/ GET `/api/v1/borrow/requests/{id}/`

## Phase 2.3：耗材与库存 API（已完成）
- 耗材 CRUD：`/api/v1/consumables/`（管理员可写，其余只读；对外字段 `current_qty` 映射数据库 `current_stock`）
- 预警：`GET /api/v1/consumables/warnings/`（`current_stock < safety_stock`）
- 入库：`POST /api/v1/stock/in/`（管理员；直接 `APPROVED`；增加库存）
- 领用申请：`POST /api/v1/stock/out/`（学生/老师；生成 `OUT + PENDING`；不扣库存）
- 审核：`POST /api/v1/stock/{id}/approve/` / `/reject/`（管理员；approve 防负库存）
- 流水查询：`GET /api/v1/stock/`（管理员全量；其余仅本人；分页）/ `GET /api/v1/stock/{id}/`

## Phase 2.4：维修 API（已完成）
- 维修单：`/api/v1/maintenance/`（列表/创建/更新；写入需要管理员或 `MAINTAINER`）
- 设备联动：创建维修单会将设备置为 `MAINTENANCE` 并写状态日志；维修 `DONE` 时设备回 `AVAILABLE` 并写状态日志

## Phase 2.5：统计报表 API（已完成，老师/管理员可读）
- 借用排行：`GET /api/v1/reports/borrow-top/`（可选 `limit/start/end`）
- 设备利用率：`GET /api/v1/reports/equipment-utilization/`（必填 `start/end`，可选 `limit/include_zero`）
- 耗材月消耗：`GET /api/v1/reports/consumable-monthly/`（可选 `year/consumable_id`）

## Phase 2.6：用户/角色管理 API（已完成，仅管理员）
- 用户：`/api/v1/users/`（CRUD）
- 启用/停用：`PATCH /api/v1/users/{id}/activate/` / `PATCH /api/v1/users/{id}/deactivate/`
- 角色：`/api/v1/roles/`（CRUD）
- 用户角色：`/api/v1/user-roles/`（创建/删除）

## Phase 3：前端（Vue3 + Vite + ElementPlus + Pinia）（已完成）
- 初始化工程与基础设施：Axios 实例、API 模块拆分、Pinia stores、Vite 代理与环境变量
- 登录鉴权：JWT 登录/刷新；Axios 拦截器 401 自动 refresh 并重放一次请求
- Layout + 路由守卫：未登录跳转 `/login`；基于角色/能力显示菜单与按钮级权限
- 业务页面：
  - 设备台账：分类 CRUD（管理员）、设备 CRUD + 过滤分页、设备详情与状态日志、状态变更
  - 借用流程：列表/新建/详情；管理员 approve/checkout/return；老师可看全量只读；学生仅本人
  - 耗材库存：耗材 CRUD（管理员）、预警、入库、领用申请、流水与审批/拒绝
  - 维修：列表/创建/更新；维修员可写、学生只读；DONE 后设备状态/日志刷新
  - 报表：借用排行/利用率/月消耗；老师/管理员可读；学生路由拦截提示
  - 管理后台：用户管理（CRUD/启用停用）、角色管理、用户角色分配
- 全局收口：统一错误提示、表单规则、分页组件封装、接口类型定义与前端 README 演示脚本

## Phase 4：联调验收 + 文档收尾（已完成）
- 联调步骤：见 `docs/ENV.md`
- 总览与入口：见根 `README.md`、`frontend/README.md`、`backend/README.md`
