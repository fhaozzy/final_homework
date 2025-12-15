# 实验室设备与耗材借用管理系统规范

## 1. 角色与权限矩阵
- **角色**：普通用户、管理员（审批/出入库/验收）、维修员（可选，若无则管理员兼任）
- **矩阵（关键能力）**  
  - 登录、刷新 token：所有角色  
  - 查看设备/耗材台账与库存：所有角色  
  - 申请设备借用、提交归还、申请耗材领用：普通用户、管理员  
  - 审批设备借用、出库、归还验收：管理员  
  - 耗材入库、耗材领用审核扣减库存、库存预警配置：管理员  
  - 维修单登记、更新：管理员、维修员  
  - 用户/角色管理：管理员  
  - 报表：管理员

## 2. 状态机
- **设备状态**：AVAILABLE → RESERVED(申请通过待出库) → OUT(已借出) → RETURN_PENDING(已归还待验收) → AVAILABLE；任意时刻可进入 MAINTENANCE；报废 DISCARDED（终态，不可再借）。  
- **借用单 borrow_request.status**：DRAFT → PENDING_APPROVAL → APPROVED → REJECTED | CANCELLED；APPROVED 后待出库，出库完成由物品行转 OUT。  
- **借用行 borrow_item.status**：PENDING → OUT → RETURN_PENDING → RETURN_ACCEPTED | RETURN_REJECTED。  
- **耗材库存事务 stock_txn.type**：IN、CONSUME；CONSUME 必须在审核通过时扣减。  
- **耗材领用申请（可用 borrow_request + item.type=CONSUMABLE）**：同借用审批，但扣减库存在管理员审核通过时原子执行。  
- **维修 maintenance.status**：OPEN → IN_PROGRESS → DONE；DONE 时设备可回 AVAILABLE。

## 3. 数据表字段建议（已用 Django Models 落地；db_table 与要求一致；主键 bigint 自增；统一 created_at/updated_at）
- **user（accounts.User）**：id, username(uniq), password(哈希), email, real_name, phone, is_active, is_staff, date_joined, created_at, updated_at  
- **role（accounts.Role）**：id, code(uniq), name, created_at, updated_at  
- **user_role（accounts.UserRole）**：id, user_id FK user, role_id FK role, created_at, updated_at；uniq(user_id,role_id)；idx(user_id), idx(role_id)  
- **equipment_category（inventory.EquipmentCategory）**：id, name(uniq), code(uniq), description, created_at, updated_at  
- **equipment（inventory.Equipment）**：id, code(uniq), name, category_id FK equipment_category, status(enum AVAILABLE/RESERVED/OUT/RETURN_PENDING/MAINTENANCE/DISCARDED), location, purchase_date, price, vendor, spec, usable, created_at, updated_at；idx(category_id), idx(status)  
- **equipment_status_log（inventory.EquipmentStatusLog）**：id, equipment_id FK equipment, from_status, to_status, changed_by FK user, reason, remark, created_at, updated_at；idx(equipment_id)  
- **borrow_request（borrowing.BorrowRequest）**：id, applicant_id FK user, type(enum EQUIPMENT/CONSUMABLE), status(enum DRAFT/PENDING_APPROVAL/APPROVED/REJECTED/CANCELLED), purpose, expected_return_date, submitted_at, approved_at, rejected_at, approver_id FK user(nullable, 固定管理员), remark, created_at, updated_at；idx(applicant_id,status,type)  
- **borrow_item（borrowing.BorrowItem）**：id, request_id FK borrow_request, item_type(enum EQUIPMENT/CONSUMABLE), equipment_id FK equipment(nullable), consumable_id FK consumable(nullable), qty(>0), status(enum PENDING/OUT/RETURN_PENDING/RETURN_ACCEPTED/RETURN_REJECTED), out_at, due_at, return_submitted_at, return_checked_at, created_at, updated_at；uniq(request_id,equipment_id)；idx(request_id,status)  
- **borrow_approval（borrowing.BorrowApproval）**：id, request_id OneToOne borrow_request, approver_id FK user, decision(enum APPROVED/REJECTED), comment, decided_at, created_at, updated_at  
- **return_record（borrowing.ReturnRecord）**：id, borrow_item_id OneToOne borrow_item, checked_by FK user, condition(enum GOOD/DAMAGED/LOST), fee, remark, checked_at, created_at, updated_at  
- **maintenance（maintenance.Maintenance）**：id, equipment_id FK equipment, title, description, status(enum OPEN/IN_PROGRESS/DONE), assigned_to FK user(nullable), cost, started_at, finished_at, created_at, updated_at；idx(equipment_id), idx(status)  
- **consumable（inventory.Consumable）**：id, code(uniq), name, unit, category, safety_stock, current_stock, location, created_at, updated_at；idx(code), idx(current_stock)  
- **stock_txn（inventory.StockTxn）**：id, consumable_id FK consumable, type(enum IN/CONSUME), qty(>0), related_request_id FK borrow_request(nullable), performed_by FK user, remark, created_at, updated_at；idx(consumable_id,type,created_at)  

> 说明：Django 自带的 `auth_*`、`django_*` 等为框架系统表，不计入上述 13 张业务表。

## 4. 关键业务规则
- 登录使用 SimpleJWT，所有接口除登录/刷新外需携带 Bearer token。  
- RBAC：请求需校验角色；管理员为唯一审批人。  
- 设备借用：仅设备状态为 AVAILABLE 可被加入借用单；审批通过后将设备状态改为 RESERVED；出库时原子更新 equipment.status=OUT + borrow_item.status=OUT + 写 status_log。  
- 归还：用户提交归还申请（borrow_item -> RETURN_PENDING），管理员验收后状态 RETURN_ACCEPTED 并将设备改回 AVAILABLE 或进入 MAINTENANCE。  
- 维修：设备进入 MAINTENANCE 时不可出库；维修完成方可回 AVAILABLE。  
- 耗材：入库使用 stock_txn(type=IN) 增加 current_stock；领用审批通过时在事务内使用 F 表达式扣减并防止负库存，写 CONSUME 事务。  
- 库存预警：current_stock < safety_stock 时标记预警或在列表标识。  
- 报表：  
  - 借用排行：按设备被借次数或时长排序。  
  - 设备利用率：OUT 时长 / 可用时长（按日志或状态变更）。  
  - 耗材月消耗：按 month(sum CONSUME.qty)。

## 5. REST 接口清单（示例路径，均返回 {code, message, data}，日期用 ISO8601）
- **认证**  
  - POST `/api/auth/login` body{username,password} → tokens{access,refresh}  
  - POST `/api/auth/refresh` body{refresh} → access
- **用户 & 角色（管理员）**  
  - GET `/api/users`，POST `/api/users`，PUT `/api/users/{id}`，PATCH `/api/users/{id}/activate`  
  - GET `/api/roles`，POST `/api/roles`，POST `/api/user-roles`  
- **设备台账**  
  - GET `/api/equipment` 查询（支持 status/category/keyword）  
  - POST `/api/equipment` 新增，PUT `/api/equipment/{id}` 更新  
  - GET `/api/equipment/{id}/logs` 状态日志  
  - POST `/api/equipment/{id}/maintenance` 创建维修单  
- **借用流程（设备/耗材共用 borrow_request）**  
  - POST `/api/borrow-requests` body{type,purpose,expected_return_date,items:[{item_type,equipment_id|consumable_id,qty,due_at}]}` → draft  
  - POST `/api/borrow-requests/{id}/submit` → PENDING_APPROVAL  
  - POST `/api/borrow-requests/{id}/approve`（管理员）body{decision,comment} → APPROVED/REJECTED；设备 APPROVED 时设备置 RESERVED  
  - POST `/api/borrow-items/{id}/out`（管理员） → status OUT，设备置 OUT  
  - POST `/api/borrow-items/{id}/return`（申请归还） → RETURN_PENDING  
  - POST `/api/borrow-items/{id}/check-return`（管理员）body{condition,fee,remark,maintenance_needed?} → RETURN_ACCEPTED/REJECTED，设备回 AVAILABLE 或 MAINTENANCE  
  - GET `/api/borrow-requests`、`/api/borrow-items` 查询
- **耗材库存**  
  - POST `/api/consumables` 新增，GET `/api/consumables` 查询  
  - POST `/api/consumables/{id}/stock-in` body{qty,remark} → stock_txn IN  
  - 审核领用（复用 approve 接口）：决策 APPROVED 时事务扣减库存 + 写 CONSUME txn；若不足则拒绝  
  - GET `/api/consumables/{id}/txns` 事务流水  
- **维修**  
  - GET `/api/maintenance`，POST `/api/maintenance`，PATCH `/api/maintenance/{id}` 更新状态  
- **报表**  
  - GET `/api/reports/borrow-top` params{range}  
  - GET `/api/reports/equipment-utilization` params{range}  
  - GET `/api/reports/consumable-monthly` params{year}

### 请求/响应示例
```json
POST /api/borrow-requests
{
  "type": "EQUIPMENT",
  "purpose": "毕业课题实验",
  "expected_return_date": "2025-01-20",
  "items": [{"item_type":"EQUIPMENT","equipment_id":101,"qty":1,"due_at":"2025-01-20"}]
}
→ 200 { "code":0, "data":{"id":9001,"status":"DRAFT"} }
```
```json
POST /api/borrow-requests/9001/approve
{ "decision":"APPROVED", "comment":"准予借用" }
→ 200 { "code":0, "data":{"status":"APPROVED"} }
```
```json
POST /api/consumables/11/stock-in
{ "qty":50, "remark":"本月采购" }
→ 200 { "code":0, "data":{"current_stock":180} }
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
3) 管理员审批通过（设备状态变 RESERVED）。  
4) 管理员出库（状态 OUT，查看状态日志）。  
5) 用户提交归还，管理员验收通过（设备回 AVAILABLE）。  
6) 管理员登记设备维修，完结维修。  
7) 管理员为耗材入库；用户提交耗材领用申请；管理员审核扣减库存，查看预警。  
8) 查看报表：借用排行、设备利用率、耗材月消耗。

## 8. 测试用例要点
- 认证：登录/刷新；过期 token 拒绝。  
- RBAC：普通用户无法访问审批/出库接口；未授权路由被拦截。  
- 设备借用：  
  - 仅 AVAILABLE 可加入申请；审批通过后变 RESERVED；出库时事务更新设备+借用行。  
  - 归还验收后状态切换正确；拒收保持 RETURN_REJECTED。  
  - MAINTENANCE 状态设备不可出库。  
- 耗材：  
  - 入库增加库存；审批时扣减库存防负数（并发下事务正确）。  
  - 安全库存预警触发。  
- 维修：设备进入 MAINTENANCE 后禁止借出；完成后可借。  
- 报表：数据范围过滤正确；借用排行/利用率计算正确。  
- 并发一致性：出库/扣库存使用事务+行锁，F 表达式验证无脏写。  
- 数据完整性：唯一约束/外键/索引验证；删除被引用记录受限或使用软删。  
- API 契约：请求校验、错误码、分页排序、生效过滤。
