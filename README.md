# 实验室设备与耗材借用管理系统

技术栈：
- 后端：Django + DRF + SimpleJWT + MySQL
- 前端：Vue3 + Vite + ElementPlus + Pinia + Axios

文档：
- 需求/权限/状态机/接口规范：`docs/SPEC.md`
- 环境与启动：`docs/ENV.md`
- 阶段进展：`docs/STATUS.md`

目录结构：
- `backend/` 后端 Django 项目
- `frontend/` 前端项目（待完善）
- `docs/` 项目文档
- `sql/` SQL 脚本（可选）

快速启动（后端）：
1. 按 `docs/ENV.md` 配置虚拟环境与 `backend/.env`
2. `cd backend && python manage.py migrate`
3. `python manage.py runserver 0.0.0.0:8000`
4. `GET http://127.0.0.1:8000/api/v1/health/` → `{"status":"ok"}`
