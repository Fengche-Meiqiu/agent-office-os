# Hermes Agent API 桥 — 接口规格书

> 本文档供 Hermes 方参考，说明 Office OS 期望 Agent API 桥（8001 端口）实现的接口规格。
> Hermes 方按此文档实现 API 桥，Office OS 方按此文档调用。

---

## 基础信息

- **API 桥地址**：`http://127.0.0.1:8001`（宿主机本地）
- **Office OS 容器访问地址**：`http://host.docker.internal:8001`
- **数据格式**：JSON
- **字符编码**：UTF-8
- **超时**：Office OS 侧设置 30 秒超时

---

## 接口清单（9 个）

### 1. GET /api/agents — 发现 Agent

Office OS 调用此接口获取 Hermes 上的全部 Agent 列表，用于人才市场展示。

**请求**：无参数

**响应**（200）：
```json
[
  {
    "id": "hermes_agent_001",
    "name": "市场分析师",
    "title": "资深市场分析师",
    "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=agent001",
    "platform": "Hermes",
    "description": "负责行业研究",
    "status": "ONLINE",
    "skills": ["市场分析", "竞品研究", "战略规划"],
    "tools": ["web_search", "python", "excel"]
  }
]
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | Agent 唯一标识，后续接口用这个 ID |
| name | string | 是 | Agent 名称 |
| title | string | 否 | 职位头衔 |
| avatar | string | 否 | 头像 URL |
| platform | string | 否 | 平台名，固定 "Hermes" |
| description | string | 否 | 简介 |
| status | string | 否 | 状态：ONLINE / OFFLINE / BUSY |
| skills | string[] | 否 | 技能列表 |
| tools | string[] | 否 | 工具列表 |

---

### 2. GET /api/agents/{agent_id} — Agent 详情

**路径参数**：`agent_id` — Agent ID

**响应**（200）：
```json
{
  "id": "hermes_agent_001",
  "name": "市场分析师",
  "role": "Market Analyst",
  "description": "负责行业研究",
  "platform": "Hermes"
}
```

---

### 3. GET /api/agents/{agent_id}/skills — 技能列表

**路径参数**：`agent_id`

**响应**（200）：
```json
["市场分析", "竞品研究", "战略规划", "数据可视化"]
```

---

### 4. GET /api/agents/{agent_id}/tools — 工具能力

**路径参数**：`agent_id`

**响应**（200）：
```json
[
  {"name": "web_search", "type": "search"},
  {"name": "python", "type": "code"},
  {"name": "shell", "type": "system"}
]
```

---

### 5. GET /api/agents/{agent_id}/memory — 记忆摘要

**路径参数**：`agent_id`

**响应**（200）：
```json
{
  "summary": "负责新能源行业研究，擅长竞品分析"
}
```

> V1 仅展示摘要，不支持编辑。

---

### 6. POST /api/agents/{agent_id}/chat — 聊天

**路径参数**：`agent_id`

**请求体**：
```json
{
  "message": "帮我分析一下新能源汽车市场"
}
```

**响应**（200）：
```json
{
  "reply": "好的，新能源汽车市场目前处于快速增长阶段..."
}
```

> Office OS 会把用户消息和 Agent 回复都存入本地数据库。Hermes 侧只需要返回回复内容。

---

### 7. POST /api/tasks — 派发任务

**请求体**：
```json
{
  "agent_id": "hermes_agent_001",
  "title": "分析新能源汽车行业",
  "content": "请分析 2024 年新能源汽车市场的竞争格局..."
}
```

**响应**（200）：
```json
{
  "task_id": "hermes_task_123"
}
```

> Office OS 收到 task_id 后会存入数据库，状态标记为 Running。后续通过 Webhook 通知任务完成。

---

### 8. GET /api/tasks/{task_id} — 查询任务状态

**路径参数**：`task_id` — 派发任务时返回的 ID

**响应 — 进行中**（200）：
```json
{
  "status": "running"
}
```

**响应 — 已完成**（200）：
```json
{
  "status": "completed",
  "result": "分析报告内容..."
}
```

**响应 — 失败**（200）：
```json
{
  "status": "failed",
  "error": "执行超时"
}
```

---

### 9. POST /api/meetings/respond — 会议发言

Office OS 在会议的每一轮讨论中，依次调用此接口让每个 Agent 发言。

**请求体**：
```json
{
  "agent_id": "hermes_agent_001",
  "meeting_id": "meeting_abc123",
  "topic": "是否投资AI行业",
  "history": [
    {"role": "agent", "content": "我认为AI行业前景广阔", "agentName": "市场分析师"},
    {"role": "agent", "content": "需要评估技术风险", "agentName": "技术专家"},
    {"role": "user", "content": "预算控制在500万以内", "agentName": "主持人"}
  ]
}
```

**响应**（200）：
```json
{
  "opinion": "综合考虑市场前景和预算限制，建议分阶段投入..."
}
```

**history 字段说明**：

| 字段 | 说明 |
|------|------|
| role | 发言者身份：`agent`（Agent）或 `user`（主持人） |
| content | 发言内容 |
| agentName | 发言者名称（主持人为"主持人"） |

> history 包含当前会议之前所有轮次的全部发言。Agent 应基于历史上下文给出本轮意见。

---

## Webhook 回调（Hermes → Office OS）

Hermes 在以下事件发生时，主动 POST 到 Office OS：

**回调地址**：`http://127.0.0.1:8000/api/webhook/hermes`
（或通过 Nginx：`http://127.0.0.1/api/webhook/hermes`）

### 支持的事件

#### task_created — 任务已创建
```json
{
  "event": "task_created",
  "task_id": "hermes_task_123",
  "agent_id": "hermes_agent_001"
}
```

#### task_started — 任务开始执行
```json
{
  "event": "task_started",
  "task_id": "hermes_task_123",
  "agent_id": "hermes_agent_001"
}
```

#### task_completed — 任务完成
```json
{
  "event": "task_completed",
  "task_id": "hermes_task_123",
  "agent_id": "hermes_agent_001",
  "status": "completed",
  "result": "分析报告内容..."
}
```

#### task_failed — 任务失败
```json
{
  "event": "task_failed",
  "task_id": "hermes_task_123",
  "agent_id": "hermes_agent_001",
  "status": "failed"
}
```

#### agent_online — Agent 上线
```json
{
  "event": "agent_online",
  "agent_id": "hermes_agent_001"
}
```

#### agent_offline — Agent 下线
```json
{
  "event": "agent_offline",
  "agent_id": "hermes_agent_001"
}
```

### Webhook 响应

Office OS 收到回调后返回：
```json
{
  "message": "回调已处理",
  "event": "task_completed"
}
```

---

## 降级处理

如果某些接口暂未实现，Office OS 会降级处理，不会崩溃：

| 接口未实现时的行为 | 影响 |
|------------------|------|
| GET /api/agents 返回空 | 人才市场为空，但种子数据仍可用 |
| POST /api/agents/{id}/chat 超时 | 聊天显示"暂时无法连接" |
| POST /api/tasks 返回空 | 任务标记为 Failed |
| POST /api/meetings/respond 超时 | Agent 发言显示"暂时无法响应" |
| Webhook 未配置 | 任务状态不会自动更新（需手动查询） |

---

## 对接验证清单

API 桥建好后，可以用以下命令快速验证：

```bash
# 1. 验证 Agent 发现
curl http://localhost:8001/api/agents

# 2. 验证聊天
curl -X POST http://localhost:8001/api/agents/hermes_agent_001/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好"}'

# 3. 验证任务派发
curl -X POST http://localhost:8001/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"hermes_agent_001","title":"测试任务","content":"测试"}'

# 4. 验证 Webhook 回调（从 Hermes 侧发起到 Office OS）
curl -X POST http://localhost:8000/api/webhook/hermes \
  -H "Content-Type: application/json" \
  -d '{"event":"agent_online","agent_id":"hermes_agent_001"}'
```

---

## 并行开发说明

- **Office OS 侧**：代码已开发完成，`HERMES_URL` 已配置为 `http://host.docker.internal:8001`
- **Hermes 侧**：按本文档实现 API 桥，监听 8001 端口
- **两边可并行开发**：Office OS 有完整的 Mock 数据，不依赖 Hermes 也能独立运行和展示
- **对接时**：只需确保 API 桥的接口格式与本文档一致即可无缝对接
