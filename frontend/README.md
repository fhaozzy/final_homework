# Lab Borrowing System - Frontend (Vue3 + Vite)

## 开发启动

- 安装依赖：`npm i`
- 配置环境变量：复制 `.env.example` 为 `.env`，按需修改 `VITE_API_BASE_URL`
- 启动开发：`npm run dev`

## 后端联调

- 默认代理：`vite.config.ts` 已将 `/api/v1` 代理到 `http://127.0.0.1:8000`（用于开发期避免 CORS）
- 后端启动后，可直接访问前端页面并调用 API（确保 `.env` 中 `VITE_API_BASE_URL=/api/v1`）
