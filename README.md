# 实验室设备与耗材借用管理系统

技术栈：
- 后端：Django + DRF + SimpleJWT + MySQL
- 前端：Vue3 + Vite + ElementPlus + Pinia + Axios

文档：
- 需求/权限/状态机/接口规范：`docs/SPEC.md`
- 环境与启动/联调验收：`docs/ENV.md`
- 阶段进展：`docs/STATUS.md`

目录结构：
- `backend/` 后端 Django 项目
- `frontend/` 前端项目（已实现核心模块）
- `docs/` 项目文档
- `sql/` SQL 脚本（可选）

快速启动（建议按文档完整走一遍）：
1. 按 `docs/ENV.md` 配置 `.venv`、`backend/.env`、`frontend/.env`
2. 启动后端：`cd backend` → `python manage.py migrate` → `python manage.py runserver 0.0.0.0:8000`
3. 启动前端：`cd frontend` → `npm i` → `npm run dev`
4. 健康检查：`GET http://127.0.0.1:8000/api/v1/health/` → `{"status":"ok"}`

联调演示脚本：
- 前端角度完整演示：`frontend/README.md`
