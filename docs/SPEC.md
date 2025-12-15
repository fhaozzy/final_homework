# 实验室设备与耗材借用管理系统规范

## 1. 角色与权限矩阵
- **角色**：普通用户、管理员（审批/出入库/验收）、维修员（可选，若无则管理员兼任）
- **矩阵（关键能力）**  
  - 登录、刷新 token：所有角色  
  - 查看设备/耗材台账与库存：所有角色  
- 申请设备借用、申请耗材领用：普通用户、管理员  
  - 审批设备借用、出库、归还验收：管理员  
  - 耗材入库、耗材领用审核扣减库存、库存预警配置：管理员  
  - 维修单登记、更新：管理员、维修员  
  - 用户/角色管理：管理员  
  - 报表：管理员

## 2. 状态机
- **设备状态（借用主流程）**：AVAILABLE → BORROWED → AVAILABLE；任意时刻可进入 MAINTENANCE；报废 DISCARDED（终态，不可再借）。  
- **借用单 borrow_request.status**：REQUESTED → APPROVED → OUT → CLOSED；REQUESTED → REJECTED。  
- **借用行 borrow_item.status**：PENDING → OUT → RETURN_ACCEPTED（本阶段由管理员验收直接闭环）。  
- **耗材库存事务 stock_txn**：type=IN（入库）|OUT（领用）；status=PENDING → APPROVED | REJECTED；OUT 在管理员 APPROVED 时才扣减库存。  
- **耗材预警**：consumable.current_qty(current_stock) < safety_stock。  
- **维修 maintenance.status**：OPEN → IN_PROGRESS → DONE；DONE 时设备可回 AVAILABLE。

## 3. 数据表字段建议（已用 Django Models 落地；db_table 与要求一致；主键 bigint 自增；统一 created_at/updated_at）
- **user（accounts.User）**：id, username(uniq), password(哈希), email, real_name, phone, is_active, is_staff, date_joined, created_at, updated_at  
- **role（accounts.Role）**：id, code(uniq), name, created_at, updated_at  
- **user_role（accounts.UserRole）**：id, user_id FK user, role_id FK role, created_at, updated_at；uniq(user_id,role_id)；idx(user_id), idx(role_id)  
- **equipment_category（inventory.EquipmentCategory）**：id, name(uniq), code(uniq), description, created_at, updated_at  
- **equipment（inventory.Equipment）**：id, code(uniq), name, category_id FK equipment_category, status(enum AVAILABLE/RESERVED/BORROWED/OUT(legacy)/RETURN_PENDING/MAINTENANCE/DISCARDED), location, purchase_date, price, vendor, spec, usable, created_at, updated_at；idx(category_id), idx(status)  
- **equipment_status_log（inventory.EquipmentStatusLog）**：id, equipment_id FK equipment, from_status, to_status, changed_by FK user, reason, remark, created_at, updated_at；idx(equipment_id)  
- **borrow_request（borrowing.BorrowRequest）**：id, applicant_id FK user, type(enum EQUIPMENT/CONSUMABLE), status(enum REQUESTED/APPROVED/REJECTED/OUT/CLOSED), purpose, expected_return_date, submitted_at, approved_at, rejected_at, approver_id FK user(nullable, 固定管理员), remark, created_at, updated_at；idx(applicant_id,status,type)  
- **borrow_item（borrowing.BorrowItem）**：id, request_id FK borrow_request, item_type(enum EQUIPMENT/CONSUMABLE), equipment_id FK equipment(nullable), consumable_id FK consumable(nullable), qty(>0), status(enum PENDING/OUT/RETURN_PENDING/RETURN_ACCEPTED/RETURN_REJECTED), out_at, due_at, return_submitted_at, return_checked_at, created_at, updated_at；uniq(request_id,equipment_id)；idx(request_id,status)  
- **borrow_approval（borrowing.BorrowApproval）**：id, request_id OneToOne borrow_request, approver_id FK user, decision(enum APPROVED/REJECTED), comment, decided_at, created_at, updated_at  
- **return_record（borrowing.ReturnRecord）**：id, borrow_item_id OneToOne borrow_item, checked_by FK user, condition(enum GOOD/DAMAGED/LOST), fee, remark, checked_at, created_at, updated_at  
- **maintenance（maintenance.Maintenance）**：id, equipment_id FK equipment, title, description, status(enum OPEN/IN_PROGRESS/DONE), assigned_to FK user(nullable), cost, started_at, finished_at, created_at, updated_at；idx(equipment_id), idx(status)  
- **consumable（inventory.Consumable）**：id, code(uniq), name, unit, category, safety_stock, current_stock, location, created_at, updated_at；idx(code), idx(current_stock)  
- **stock_txn（inventory.StockTxn）**：id, consumable_id FK consumable, type(enum IN/OUT), status(enum PENDING/APPROVED/REJECTED), qty(>0), related_request_id FK borrow_request(nullable), performed_by FK user, reviewed_by FK user(nullable), decided_at(nullable), remark, created_at, updated_at；idx(consumable_id,type,created_at), idx(status)  

> 说明：Django 自带的 `auth_*`、`django_*` 等为框架系统表，不计入上述 13 张业务表。

## 4. 关键业务规则
- 登录使用 SimpleJWT，所有接口除登录/刷新外需携带 Bearer token。  
- RBAC：请求需校验角色；管理员为唯一审批人。  
- 设备借用：创建申请时校验设备为 AVAILABLE；管理员 approve 后 request→APPROVED（本阶段不改设备状态）；管理员 checkout 时事务 + 行锁，确保仅 AVAILABLE 可出库，并将设备→BORROWED、borrow_item→OUT、request→OUT，同时写入 equipment_status_log。  
- 归还验收：管理员 return 时写 ReturnRecord，并将设备→AVAILABLE、borrow_item→RETURN_ACCEPTED、request→CLOSED，同时写入 equipment_status_log。  
- 维修：设备进入 MAINTENANCE 时不可出库；维修完成方可回 AVAILABLE。  
- 耗材：
  - 入库：管理员创建 stock_txn(IN,APPROVED)，并增加 current_stock（事务内更新）。
  - 领用：学生/老师创建 stock_txn(OUT,PENDING)，不扣库存；管理员审核 APPROVED 时在事务内（行锁/F 表达式）扣减 current_stock，若库存不足则审核失败且不改动库存。
- 库存预警：current_stock < safety_stock 时标记预警或在列表标识。  
- 报表：  
  - 借用排行：按设备被借次数或时长排序。  
  - 设备利用率：OUT 时长 / 可用时长（按日志或状态变更）。  
  - 耗材月消耗：按 month(sum OUT.qty where status=APPROVED)。

## 5. REST 接口清单（示例路径，JSON；日期用 ISO8601）
- **认证**  
  - POST `/api/v1/auth/token/` body{username,password} → tokens{access,refresh}  
  - POST `/api/v1/auth/token/refresh/` body{refresh} → access
- **用户 & 角色（管理员）**  
  - GET `/api/users`，POST `/api/users`，PUT `/api/users/{id}`，PATCH `/api/users/{id}/activate`  
  - GET `/api/roles`，POST `/api/roles`，POST `/api/user-roles`  
- **设备台账**  
  - 设备分类：`/api/v1/equipment-categories/`（CRUD；非管理员只读）  
  - 设备台账：`/api/v1/equipment/`（CRUD；支持 status/category/keyword 过滤 + 分页；非管理员只读）  
  - 状态变更：POST `/api/v1/equipment/{id}/status/`（管理员）  
  - 状态日志：GET `/api/v1/equipment/{id}/logs/`  
- **借用流程（设备借用 v1，严格按状态机）**  
  - POST `/api/v1/borrow/requests/`（学生/老师）→ 创建 borrow_request + borrow_item，状态 `REQUESTED`  
  - POST `/api/v1/borrow/requests/{id}/approve/`（管理员）→ `APPROVED`，写 `borrow_approval`  
  - POST `/api/v1/borrow/requests/{id}/reject/`（管理员）→ `REJECTED`，写 `borrow_approval`  
  - POST `/api/v1/borrow/requests/{id}/checkout/`（管理员）→ 事务 + 行锁；仅 `AVAILABLE` 可出库；设备→`BORROWED`；写 `equipment_status_log`；request→`OUT`  
  - POST `/api/v1/borrow/requests/{id}/return/`（管理员）→ 写 `return_record`；设备→`AVAILABLE`；写 `equipment_status_log`；request→`CLOSED`  
  - GET `/api/v1/borrow/requests/`（管理员全量；普通用户仅自己）/ GET `/api/v1/borrow/requests/{id}/`
- **耗材库存**  
  - 耗材：`/api/v1/consumables/`（CRUD；非管理员只读）  
  - 预警：GET `/api/v1/consumables/warnings/`  
  - 入库：POST `/api/v1/stock/in/`（管理员；直接 APPROVED；增加库存）  
  - 领用申请：POST `/api/v1/stock/out/`（学生/老师；OUT + PENDING；不扣库存）  
  - 审核：POST `/api/v1/stock/{id}/approve/` / POST `/api/v1/stock/{id}/reject/`（管理员；approve 防负库存）  
- **维修**  
  - GET `/api/maintenance`，POST `/api/maintenance`，PATCH `/api/maintenance/{id}` 更新状态  
- **报表**  
  - GET `/api/v1/reports/borrow-top/` params{limit,start?,end?}  
  - GET `/api/v1/reports/equipment-utilization/` params{start,end,limit?,include_zero?}  
  - GET `/api/v1/reports/consumable-monthly/` params{year?,consumable_id?}

### 请求/响应示例
```json
POST /api/v1/borrow/requests/
{
  "purpose": "毕业课题实验",
  "expected_return_date": "2025-01-20",
  "items": [{"equipment_id":101},{"equipment_id":102}]
}
→ 201 { "id":9001, "status":"REQUESTED", "items":[...] }
```
```json
POST /api/v1/borrow/requests/9001/approve/
{ "comment":"准予借用" }
→ 200 { "status":"APPROVED" }
```
```json
POST /api/v1/stock/in/
{ "consumable_id": 11, "qty": 50, "remark": "本月采购" }
→ 201 { "id": 1, "consumable_id": 11, "type": "IN", "status": "APPROVED", "qty": 50 }
```
```json
GET /api/v1/reports/borrow-top/?limit=10
→ 200 {
  "limit": 10,
  "range": {"start": null, "end": null},
  "items": [{"equipment_id": 1, "equipment_code": "E-001", "equipment_name": "示波器", "borrow_count": 3}]
}
```
```json
GET /api/v1/reports/equipment-utilization/?start=2025-12-01&end=2025-12-31
→ 200 {
  "range": {"start":"2025-12-01","end":"2025-12-31","range_days":31},
  "items": [{"equipment_id": 1, "equipment_code": "E-001", "borrowed_days": 5, "range_days": 31, "utilization_rate": 0.16129}]
}
```
```json
GET /api/v1/reports/consumable-monthly/?year=2025
→ 200 {
  "year": 2025,
  "items": [{"month":"2025-01","qty":0},{"month":"2025-02","qty":12}]
}
```

## 6. 前端页面清单与路由（Vue3 + Vite + ElementPlus + Pinia）
- `/login` 登录页  
- `/dashboard` 仪表盘（预警、今日审批、统计卡片）  
- `/equipment` 设备台账列表；`/equipment/:id` 详情+状态日志+维修记录  
- `/borrow/requests` 借用申请列表（含耗材）；`/borrow/new` 创建；`/borrow/:id` 详情+审批+出库+归还验收  
- `/consumables` 耗材与库存；`/consumables/:id` 流水；`/consumables/stock-in` 入库  
- `/maintenance` 维修单列表/编辑  
- `/reports/borrow-top`，`/reports/utilization`，`/reports/consumption`  
- `/admin/users` 用户管理；`/admin/roles` 角色管理  
- 导航基于角色动态过滤；路由守卫校验 token & 角色。

## 7. 演示脚本（示例）
1) 管理员登录。  
2) 用户创建设备借用申请并提交。  
3) 管理员审批通过（request 状态变 APPROVED）。  
4) 管理员出库（request→OUT；设备→BORROWED；查看状态日志）。  
5) 管理员归还验收（request→CLOSED；设备回 AVAILABLE）。  
6) 管理员登记设备维修，完结维修。  
7) 管理员为耗材入库；用户提交耗材领用申请；管理员审核扣减库存，查看预警。  
8) 查看报表：借用排行、设备利用率、耗材月消耗。

## 8. 测试用例要点
- 认证：登录/刷新；过期 token 拒绝。  
- RBAC：普通用户无法访问审批/出库接口；未授权路由被拦截。  
- 设备借用：  
  - 仅 AVAILABLE 可加入申请；approve 后 request=APPROVED；checkout 时事务更新设备(BORROWED)+借用行(OUT)+request(OUT)。  
  - 归还验收后：request=CLOSED、borrow_item=RETURN_ACCEPTED、return_record 生成、设备回 AVAILABLE。  
  - MAINTENANCE 状态设备不可出库。  
- 耗材：  
  - 入库增加库存；审批时扣减库存防负数（并发下事务正确）。  
  - 安全库存预警触发。  
- 维修：设备进入 MAINTENANCE 后禁止借出；完成后可借。  
- 报表：数据范围过滤正确；借用排行/利用率计算正确。  
- 并发一致性：出库/扣库存使用事务+行锁，F 表达式验证无脏写。  
- 数据完整性：唯一约束/外键/索引验证；删除被引用记录受限或使用软删。  
- API 契约：请求校验、错误码、分页排序、生效过滤。
