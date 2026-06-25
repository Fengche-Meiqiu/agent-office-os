# Agent Office OS 部署操作手册

> 本手册供 Hermes（服务器管理员）参考，包含项目说明、部署步骤、配合事项清单。

---

## 一、项目概述

### 1.1 Agent Office OS 是什么

Agent Office OS 是一个**虚拟办公室管理系统**，用于管理来自 Hermes 等平台的 Agent。

核心定位：
- Office OS 是 **Agent 的组织管理层**（管雇佣、工位、任务、会议、成果）
- Hermes 是 **Agent 的运行引擎**（Agent 实际执行在 Hermes 上）
- 两者通过 **REST API + Webhook** 双向通信

### 1.2 系统架构

```
用户浏览器
    ↓ HTTP
Nginx (端口 80)
    ├── /          → 前端静态文件（React 打包产物）
    └── /api/      → 后端 API（FastAPI，端口 8000）
                        ↓ HTTP
                    Hermes（已部署）
                        ↓ Webhook 回调
                    POST /api/webhook/hermes
```

### 1.3 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 前端 | React + TypeScript + Vite | React 18 / Vite 6 |
| 后端 | Python FastAPI + SQLAlchemy | Python 3.11+ / FastAPI 0.115 |
| 数据库 | SQLite（文件型，零额外进程） | - |
| 反向代理 | Nginx | Alpine 版 |
| 部署 | Docker Compose | - |

### 1.4 资源占用预估

| 组件 | 内存 | 磁盘 |
|------|------|------|
| Office 后端（FastAPI + Uvicorn） | ~150MB | ~50MB（代码+依赖） |
| Nginx | ~20MB | ~50MB（镜像） |
| SQLite 数据库 | ~10MB | 随数据增长 |
| 前端静态文件 | - | ~20MB |
| **合计** | **~180MB** | **~140MB** |

服务器剩余 2.3G 内存 / 22G 磁盘，完全够用。

---

## 二、代码结构

```
Agent Office  OS/
├── src/                        # 前端源码（React + TypeScript）
├── backend/                    # 后端源码（Python FastAPI）
│   ├── app/
│   │   ├── main.py             # FastAPI 入口
│   │   ├── config.py           # 配置（Hermes 地址等）
│   │   ├── database.py         # 数据库连接
│   │   ├── models/             # 数据库表定义（10 张表）
│   │   ├── schemas/            # API 请求/响应模型
│   │   ├── api/                # 路由（9 个模块）
│   │   │   ├── marketplace.py  # 人才市场（发现/雇佣 Agent）
│   │   │   ├── office.py       # 办公室（Agent 列表/详情/解雇）
│   │   │   ├── chat.py         # 聊天（转发 Hermes）
│   │   │   ├── tasks.py        # 任务（派发给 Hermes）
│   │   │   ├── meetings.py     # 会议（多轮讨论+纪要）
│   │   │   ├── outputs.py      # 成果管理
│   │   │   ├── organization.py # 组织架构
│   │   │   ├── webhook.py      # 接收 Hermes 回调
│   │   │   └── event_logs.py   # 系统事件
│   │   ├── adapters/
│   │   │   └── hermes.py       # Hermes 适配器（9 个标准接口）
│   │   └── seed.py             # 种子数据初始化
│   ├── Dockerfile              # 后端 Docker 镜像
│   └── requirements.txt        # Python 依赖
├── docker-compose.yml          # Docker Compose 编排
├── nginx.conf                  # Nginx 反向代理配置
├── .env.production             # 生产环境变量
└── package.json                # 前端依赖与构建命令
```

---

## 三、Hermes 需要配合的事项清单

### 3.1 Hermes 需要提供的 API 接口（9 个）

Office OS 通过 `HermesAdapter` 调用以下接口。请确保 Hermes 已实现并可用：

| # | 方法 | 路径 | 请求体 | 返回 | 用途 |
|---|------|------|--------|------|------|
| 1 | GET | `/api/agents` | - | `[{id, name, description, status, title, avatar, platform, skills, tools}]` | 发现 Agent |
| 2 | GET | `/api/agents/{agent_id}` | - | `{id, name, role, description, platform}` | Agent 详情 |
| 3 | GET | `/api/agents/{agent_id}/skills` | - | `["市场分析", "Python开发"]` | 技能列表 |
| 4 | GET | `/api/agents/{agent_id}/tools` | - | `[{name, type}]` | 工具能力 |
| 5 | GET | `/api/agents/{agent_id}/memory` | - | `{summary: "..."}` | 记忆摘要 |
| 6 | POST | `/api/agents/{agent_id}/chat` | `{message: "..."}` | `{reply: "..."}` | 聊天 |
| 7 | POST | `/api/tasks` | `{agent_id, title, content}` | `{task_id: "..."}` | 派发任务 |
| 8 | GET | `/api/tasks/{task_id}` | - | `{status: "running"}` 或 `{status: "completed", result: "..."}` | 查询任务 |
| 9 | POST | `/api/meetings/respond` | `{agent_id, meeting_id, topic, history: []}` | `{opinion: "..."}` | 会议发言 |

> **说明**：如果 Hermes 暂未实现某个接口，Office OS 会降级处理（返回空数据或默认提示），不会崩溃。但功能会受限。

### 3.2 Hermes 需要配置 Webhook 回调

Hermes 在以下事件发生时，主动 POST 通知 Office OS：

**回调地址**：`http://<office-os-ip>:8000/api/webhook/hermes`
（或通过 Nginx：`http://<服务器IP>/api/webhook/hermes`）

**支持的回调事件**：

| 事件 | 说明 | payload 示例 |
|------|------|-------------|
| `task_created` | 任务已创建 | `{"event":"task_created","task_id":"123","agent_id":"001"}` |
| `task_started` | 任务开始执行 | `{"event":"task_started","task_id":"123","agent_id":"001"}` |
| `task_completed` | 任务完成 | `{"event":"task_completed","task_id":"123","agent_id":"001","status":"completed","result":"..."}` |
| `task_failed` | 任务失败 | `{"event":"task_failed","task_id":"123","agent_id":"001","status":"failed"}` |
| `agent_online` | Agent 上线 | `{"event":"agent_online","agent_id":"001"}` |
| `agent_offline` | Agent 下线 | `{"event":"agent_offline","agent_id":"001"}` |

### 3.3 网络互通要求

- Office OS 后端容器需要访问 Hermes API（出站请求）
- Hermes 需要访问 Office OS 的 Webhook 接口（入站请求）
- 如果两者在同一台服务器：
  - Hermes 在宿主机运行 → Office 容器用 `host.docker.internal` 访问
  - Hermes 在 Docker 中运行 → 用容器名访问

---

## 四、部署步骤

### 4.1 前置条件

- 服务器已安装 Docker 和 Docker Compose
- Hermes 已部署并运行
- 项目代码已上传到服务器（建议路径：`/opt/agent-office-os`）

### 4.2 第一步：构建前端

在本地或服务器上执行：

```bash
# 1. 安装前端依赖
npm install

# 2. 构建生产版本（会输出到 dist/ 目录）
npm run build

# 3. 将构建产物复制到 nginx 挂载目录
mkdir -p frontend-dist
cp -r dist/* frontend-dist/
```

### 4.3 第二步：修改配置

#### 4.3.1 修改 Hermes 地址

编辑 `docker-compose.yml`，修改 `HERMES_URL`：

```yaml
environment:
  - HERMES_URL=http://host.docker.internal:8001  # 改为 Hermes 实际地址
```

- 如果 Hermes 在宿主机直接运行：`http://host.docker.internal:<端口>`
- 如果 Hermes 在 Docker 中运行：`http://<hermes容器名>:<端口>`
- 如果 Hermes 在其他服务器：`http://<IP>:<端口>`

#### 4.3.2 修改前端 API 地址（如需要）

编辑 `.env.production`：

```env
VITE_USE_MOCK=false
VITE_API_BASE=http://<服务器IP>   # 如果通过 Nginx 代理，用服务器 IP 即可
```

> 如果前端和后端通过同一个 Nginx 暴露（推荐），`VITE_API_BASE` 可以留空或设为空字符串，前端会使用相对路径。

### 4.4 第三步：启动服务

```bash
# 在项目根目录执行
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

### 4.5 第四步：验证部署

```bash
# 1. 检查后端健康状态
curl http://localhost:8000/api/health
# 预期返回：{"status":"ok","app":"Agent Office OS","env":"production"}

# 2. 检查 API 文档
curl http://localhost:8000/docs
# 或浏览器打开 http://<服务器IP>:8000/docs

# 3. 检查前端页面
curl http://localhost/
# 或浏览器打开 http://<服务器IP>/

# 4. 检查 Agent 列表（验证 Hermes 连通性）
curl http://localhost:8000/api/marketplace/agents
```

### 4.6 第五步：Hermes 配置 Webhook 回调

在 Hermes 中配置 Webhook 回调地址为：

```
http://<office-backend容器IP>:8000/api/webhook/hermes
```

或通过 Nginx：

```
http://<服务器IP>/api/webhook/hermes
```

---

## 五、日常运维命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f office-backend
docker-compose logs -f nginx

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新代码后重新部署
docker-compose down
docker-compose up -d --build

# 备份数据库
docker cp office-backend:/app/data/office.db ./backup-$(date +%Y%m%d).db

# 恢复数据库
docker cp ./backup-20260623.db office-backend:/app/data/office.db
docker-compose restart office-backend
```

---

## 六、端口规划

| 服务 | 容器内端口 | 宿主机端口 | 说明 |
|------|-----------|-----------|------|
| Nginx | 80 | 80 | 前端 + API 反向代理 |
| Office Backend | 8000 | 8000 | FastAPI 后端（可直接访问 /docs 调试） |
| Hermes | - | 8001（或其他） | 已部署，不需要改动 |

> 如果 80 端口被占用，修改 `docker-compose.yml` 中 nginx 的端口映射，如 `"8080:80"`。

---

## 七、数据持久化

| 数据 | 容器路径 | Docker Volume | 说明 |
|------|---------|---------------|------|
| SQLite 数据库 | `/app/data/office.db` | `office-data` | Agent、任务、会议、聊天等全部数据 |
| 上传文件 | `/app/storage/` | `office-storage` | 成果文件、上传文档 |

> 即使容器删除重建，数据也不会丢失（存在 Docker Volume 中）。

---

## 八、故障排查

### 8.1 前端页面空白

```bash
# 检查前端文件是否正确挂载
docker exec office-nginx ls /usr/share/nginx/html

# 检查 Nginx 配置
docker exec office-nginx cat /etc/nginx/conf.d/default.conf
```

### 8.2 API 返回 502

```bash
# 检查后端是否正常
docker-compose logs office-backend

# 检查后端健康
curl http://localhost:8000/api/health
```

### 8.3 Agent 列表为空

```bash
# 检查 Hermes 连通性
docker exec office-backend curl -s $HERMES_URL/api/agents

# 如果返回为空，说明 Hermes API 不可达或未实现
# 检查 HERMES_URL 配置是否正确
docker exec office-backend env | grep HERMES
```

### 8.4 Webhook 回调不生效

```bash
# 检查 Webhook 接口是否可访问
curl -X POST http://localhost:8000/api/webhook/hermes \
  -H "Content-Type: application/json" \
  -d '{"event":"agent_online","agent_id":"001"}'

# 预期返回：{"message":"回调已处理","event":"agent_online"}
```

---

## 九、Hermes 配合事项总结（Checklist）

部署前请 Hermes 确认以下事项：

- [ ] **1. API 接口已就绪**：9 个标准 API（见 3.1 节）可访问
- [ ] **2. Agent 发现接口返回数据**：`GET /api/agents` 能返回 Agent 列表
- [ ] **3. 聊天接口可用**：`POST /api/agents/{id}/chat` 能返回回复
- [ ] **4. 任务接口可用**：`POST /api/tasks` 能接收并执行任务
- [ ] **5. 会议接口可用**：`POST /api/meetings/respond` 能返回发言
- [ ] **6. Webhook 已配置**：任务状态变更和 Agent 上下线时回调 Office OS
- [ ] **7. 网络互通**：Office OS 容器能访问 Hermes，Hermes 能访问 Office OS Webhook
- [ ] **8. 确认 Hermes 端口**：告知 Office OS 部署方 Hermes 的实际监听端口

---

## 十、快速部署（一键脚本）

如果以上都已确认，在服务器上执行：

```bash
# 1. 进入项目目录
cd /opt/agent-office-os

# 2. 构建前端
npm install && npm run build
mkdir -p frontend-dist && cp -r dist/* frontend-dist/

# 3. 修改 HERMES_URL（按实际修改）
# sed -i 's|http://host.docker.internal:8001|http://实际地址|' docker-compose.yml

# 4. 启动
docker-compose up -d

# 5. 验证
curl http://localhost/api/health
curl http://localhost:8000/api/marketplace/agents
```

部署完成后浏览器访问 `http://<服务器IP>` 即可使用。
