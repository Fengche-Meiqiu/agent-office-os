"""
种子数据初始化
首次启动时往数据库写入演示数据，让前端开箱即用
"""
from datetime import datetime, timedelta
import uuid
from app.database import SessionLocal
from app.models import (
    AgentMarketplace, OfficeAgent, AgentMapping, Task,
    Meeting, ChatMessage, Output, EventLog,
)


def _id(prefix: str) -> str:
    """生成带前缀的短 ID"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def init_seed_data():
    """
    初始化种子数据
    只在数据库为空时执行，避免重复写入
    """
    db = SessionLocal()
    try:
        # 如果人才市场已有数据，说明已初始化过，直接跳过
        if db.query(AgentMarketplace).count() > 0:
            return

        print("[种子数据] 开始初始化...")

        # ===== 1. 人才市场 Agent（8 个）=====
        marketplace_agents = [
            AgentMarketplace(
                id="market_001",
                name="林墨",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=LinMo&backgroundColor=b6e3f4",
                title="资深市场分析师",
                platform="Hermes",
                skills=["市场分析", "竞品研究", "战略规划", "数据可视化"],
                tools=["web_search", "python", "excel"],
                status="ONLINE",
                description="5年市场研究经验，擅长行业分析与战略规划。",
            ),
            AgentMarketplace(
                id="market_002",
                name="陈雪",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=ChenXue&backgroundColor=ffd5dc",
                title="高级财务顾问",
                platform="Hermes",
                skills=["财务分析", "风控管理", "投资评估", "报表审计"],
                tools=["python", "excel", "database"],
                status="ONLINE",
                description="注册会计师，擅长企业财务分析与风险评估。",
            ),
            AgentMarketplace(
                id="market_003",
                name="赵磊",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=ZhaoLei&backgroundColor=c0aede",
                title="全栈工程师",
                platform="Hermes",
                skills=["Python开发", "系统架构", "DevOps", "数据库设计"],
                tools=["python", "shell", "ssh", "database"],
                status="ONLINE",
                description="10年开发经验，精通后端架构与运维自动化。",
            ),
            AgentMarketplace(
                id="market_004",
                name="王芳",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=WangFang&backgroundColor=d1f4c6",
                title="供应链专家",
                platform="Hermes",
                skills=["供应链优化", "物流管理", "采购策略", "库存控制"],
                tools=["excel", "python", "browser"],
                status="ONLINE",
                description="前世界500强供应链总监，擅长端到端供应链优化。",
            ),
            AgentMarketplace(
                id="market_005",
                name="李明",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=LiMing&backgroundColor=ffdfbf",
                title="产品经理",
                platform="Hermes",
                skills=["产品设计", "需求分析", "用户研究", "项目管理"],
                tools=["browser", "email", "mcp"],
                status="OFFLINE",
                description="资深产品经理，擅长从0到1的产品搭建。",
            ),
            AgentMarketplace(
                id="market_006",
                name="张静",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=ZhangJing&backgroundColor=c0f4d6",
                title="UI/UX设计师",
                platform="Hermes",
                skills=["UI设计", "UX研究", "交互设计", "原型制作"],
                tools=["browser", "mcp"],
                status="ONLINE",
                description="获奖设计师，注重用户体验与视觉细节。",
            ),
            AgentMarketplace(
                id="market_007",
                name="刘强",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=LiuQiang&backgroundColor=b6e3f4",
                title="数据科学家",
                platform="Hermes",
                skills=["机器学习", "数据挖掘", "统计分析", "数据可视化"],
                tools=["python", "database", "shell"],
                status="BUSY",
                description="统计学博士，擅长预测建模与数据驱动决策。",
            ),
            AgentMarketplace(
                id="market_008",
                name="周伟",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=ZhouWei&backgroundColor=ffd5dc",
                title="制造优化专家",
                platform="Hermes",
                skills=["精益生产", "工艺优化", "质量管理", "设备维护"],
                tools=["python", "shell", "ssh"],
                status="ONLINE",
                description="工业工程硕士，擅长制造业流程优化与降本增效。",
            ),
        ]
        db.add_all(marketplace_agents)

        # ===== 2. 已雇佣办公室 Agent（4 个）=====
        now = datetime.utcnow()
        office_agents = [
            OfficeAgent(
                id="office_001",
                marketplace_id="market_001",
                name="林墨",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=LinMo&backgroundColor=b6e3f4",
                title="资深市场分析师",
                platform="Hermes",
                platform_agent_id="hermes_agent_001",
                status="ONLINE",
                hired_at=now - timedelta(days=30),
                last_active_at=now - timedelta(hours=1),
                department="市场部",
                soul={
                    "identity": "市场分析师",
                    "goal": "为企业提供精准的市场洞察与战略建议",
                    "principles": "数据驱动、客观中立、前瞻性思考",
                    "style": "严谨细致，善于从数据中发现规律",
                    "description": "一位经验丰富的市场分析师，擅长行业研究与竞品分析。",
                },
                skills=["市场分析", "竞品研究", "战略规划", "数据可视化"],
                tools=["web_search", "python", "excel"],
                memory=["负责新能源行业研究", "完成Q3市场竞品分析报告"],
                performance={"totalTasks": 28, "successTasks": 26, "failedTasks": 2, "meetingCount": 8},
            ),
            OfficeAgent(
                id="office_002",
                marketplace_id="market_002",
                name="陈雪",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=ChenXue&backgroundColor=ffd5dc",
                title="高级财务顾问",
                platform="Hermes",
                platform_agent_id="hermes_agent_002",
                status="WORKING",
                hired_at=now - timedelta(days=25),
                last_active_at=now - timedelta(minutes=30),
                department="财务部",
                soul={
                    "identity": "财务顾问",
                    "goal": "保障企业财务健康与合规",
                    "principles": "严谨合规、风险优先、价值创造",
                    "style": "细致入微，数字敏感",
                    "description": "注册会计师，擅长财务分析与风控管理。",
                },
                skills=["财务分析", "风控管理", "投资评估", "报表审计"],
                tools=["python", "excel", "database"],
                memory=["负责年度财务审计", "建立风控预警模型"],
                performance={"totalTasks": 22, "successTasks": 21, "failedTasks": 1, "meetingCount": 5},
            ),
            OfficeAgent(
                id="office_003",
                marketplace_id="market_003",
                name="赵磊",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=ZhaoLei&backgroundColor=c0aede",
                title="全栈工程师",
                platform="Hermes",
                platform_agent_id="hermes_agent_003",
                status="ONLINE",
                hired_at=now - timedelta(days=20),
                last_active_at=now - timedelta(hours=2),
                department="技术部",
                soul={
                    "identity": "全栈工程师",
                    "goal": "构建稳定高效的系统架构",
                    "principles": "代码质量优先、可维护性、性能导向",
                    "style": "务实高效，追求极致",
                    "description": "10年开发经验，精通后端架构与运维。",
                },
                skills=["Python开发", "系统架构", "DevOps", "数据库设计"],
                tools=["python", "shell", "ssh", "database"],
                memory=["负责服务器运维", "搭建CI/CD流水线"],
                performance={"totalTasks": 35, "successTasks": 33, "failedTasks": 2, "meetingCount": 6},
            ),
            OfficeAgent(
                id="office_004",
                marketplace_id="market_004",
                name="王芳",
                avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=WangFang&backgroundColor=d1f4c6",
                title="供应链专家",
                platform="Hermes",
                platform_agent_id="hermes_agent_004",
                status="MEETING",
                hired_at=now - timedelta(days=15),
                last_active_at=now - timedelta(minutes=10),
                department="运营部",
                soul={
                    "identity": "供应链专家",
                    "goal": "打造高效韧性的供应链体系",
                    "principles": "全局视角、数据驱动、持续优化",
                    "style": "系统思维，注重协同",
                    "description": "前500强供应链总监，擅长端到端优化。",
                },
                skills=["供应链优化", "物流管理", "采购策略", "库存控制"],
                tools=["excel", "python", "browser"],
                memory=["负责供应链流程优化", "建立供应商评估体系"],
                performance={"totalTasks": 18, "successTasks": 17, "failedTasks": 1, "meetingCount": 4},
            ),
        ]
        db.add_all(office_agents)

        # ===== 3. 平台映射 =====
        mappings = [
            AgentMapping(office_agent_id="office_001", platform="Hermes", platform_agent_id="hermes_agent_001"),
            AgentMapping(office_agent_id="office_002", platform="Hermes", platform_agent_id="hermes_agent_002"),
            AgentMapping(office_agent_id="office_003", platform="Hermes", platform_agent_id="hermes_agent_003"),
            AgentMapping(office_agent_id="office_004", platform="Hermes", platform_agent_id="hermes_agent_004"),
        ]
        db.add_all(mappings)

        # ===== 4. 历史任务（6 条）=====
        tasks = [
            Task(id="task_001", name="新能源汽车市场调研", agent_id="office_001", agent_name="林墨",
                 status="Completed", started_at=now-timedelta(days=5), ended_at=now-timedelta(days=4),
                 duration=120, output_id="output_001"),
            Task(id="task_002", name="Q3财务报表分析", agent_id="office_002", agent_name="陈雪",
                 status="Completed", started_at=now-timedelta(days=3), ended_at=now-timedelta(days=3),
                 duration=90, output_id="output_002"),
            Task(id="task_003", name="服务器架构优化", agent_id="office_003", agent_name="赵磊",
                 status="Running", started_at=now-timedelta(hours=2)),
            Task(id="task_004", name="供应链流程梳理", agent_id="office_004", agent_name="王芳",
                 status="Completed", started_at=now-timedelta(days=7), ended_at=now-timedelta(days=6),
                 duration=180, output_id="output_003"),
            Task(id="task_005", name="竞品功能对比", agent_id="office_001", agent_name="林墨",
                 status="Failed", started_at=now-timedelta(days=2), ended_at=now-timedelta(days=2),
                 duration=60),
            Task(id="task_006", name="风控模型搭建", agent_id="office_002", agent_name="陈雪",
                 status="Pending"),
        ]
        db.add_all(tasks)

        # ===== 5. 会议记录（1 条已完成）=====
        meeting = Meeting(
            id="meeting_001",
            topic="Q4战略规划讨论",
            agent_ids=["office_001", "office_002", "office_003"],
            status="finished",
            rounds=[
                {
                    "round": 1, "name": "独立意见",
                    "messages": [
                        {"role": "agent", "agentId": "office_001", "agentName": "林墨", "content": "建议加大新能源赛道投入。", "timestamp": (now-timedelta(days=1)).isoformat()},
                        {"role": "agent", "agentId": "office_002", "agentName": "陈雪", "content": "需评估资金风险。", "timestamp": (now-timedelta(days=1)).isoformat()},
                        {"role": "agent", "agentId": "office_003", "agentName": "赵磊", "content": "技术架构需提前规划。", "timestamp": (now-timedelta(days=1)).isoformat()},
                    ]
                }
            ],
            summary="关于Q4战略规划，团队一致同意在控制风险的前提下加大新能源投入。",
            decisions=["决策一：加大新能源赛道投入", "决策二：建立专项风控小组"],
            actions=["林墨负责市场调研", "陈雪负责资金规划", "赵磊负责技术选型"],
            created_at=now-timedelta(days=1),
        )
        db.add(meeting)

        # ===== 6. 成果文件（8 条）=====
        outputs = [
            Output(id="output_001", name="新能源汽车市场调研报告.md", type="markdown", source="task",
                   content="# 新能源汽车市场调研报告\n\n## 一、市场概况\n\n2024年新能源汽车市场持续增长...\n\n## 二、竞争格局\n\n主要玩家包括...",
                   created_at=now-timedelta(days=4)),
            Output(id="output_002", name="Q3财务分析报告.md", type="markdown", source="task",
                   content="# Q3财务分析报告\n\n## 营收概况\n\nQ3营收同比增长15%...",
                   created_at=now-timedelta(days=3)),
            Output(id="output_003", name="供应链流程图.html", type="html", source="task",
                   content="<h1>供应链流程图</h1><p>从采购到交付的完整流程...</p>",
                   created_at=now-timedelta(days=6)),
            Output(id="output_004", name="Q4战略规划会议纪要.md", type="markdown", source="meeting",
                   content="# Q4战略规划讨论 会议纪要\n\n## 参会人\n\n林墨、陈雪、赵磊\n\n## 决策\n\n- 加大新能源投入\n- 建立风控小组",
                   created_at=now-timedelta(days=1)),
            Output(id="output_005", name="竞品功能对比表.xlsx", type="link", source="task",
                   url="https://example.com/competitor-analysis.xlsx",
                   created_at=now-timedelta(days=2)),
            Output(id="output_006", name="系统架构图.png", type="image", source="task",
                   url="https://api.dicebear.com/7.x/shapes/svg?seed=arch",
                   created_at=now-timedelta(days=5)),
            Output(id="output_007", name="风控模型说明.md", type="markdown", source="task",
                   content="# 风控模型说明\n\n## 模型概述\n\n基于历史数据构建的风控预警模型...",
                   created_at=now-timedelta(days=7)),
            Output(id="output_008", name="用户调研报告.pdf", type="pdf", source="upload",
                   url="https://example.com/user-research.pdf",
                   created_at=now-timedelta(days=8)),
        ]
        db.add_all(outputs)

        # ===== 7. 聊天记录（12 条）=====
        chats = [
            ChatMessage(id="chat_001", agent_id="office_001", role="user", content="帮我分析一下新能源市场", timestamp=now-timedelta(hours=5)),
            ChatMessage(id="chat_002", agent_id="office_001", role="agent", content="好的，我来为您分析新能源汽车市场的最新趋势...", timestamp=now-timedelta(hours=5)),
            ChatMessage(id="chat_003", agent_id="office_001", role="user", content="主要竞争对手有哪些？", timestamp=now-timedelta(hours=4)),
            ChatMessage(id="chat_004", agent_id="office_001", role="agent", content="目前主要竞争对手包括比亚迪、特斯拉、蔚来等...", timestamp=now-timedelta(hours=4)),
            ChatMessage(id="chat_005", agent_id="office_002", role="user", content="Q3财务状况如何？", timestamp=now-timedelta(hours=3)),
            ChatMessage(id="chat_006", agent_id="office_002", role="agent", content="Q3营收同比增长15%，净利润率提升至12%...", timestamp=now-timedelta(hours=3)),
            ChatMessage(id="chat_007", agent_id="office_003", role="user", content="服务器架构有什么优化建议？", timestamp=now-timedelta(hours=2)),
            ChatMessage(id="chat_008", agent_id="office_003", role="agent", content="建议引入微服务架构，并优化数据库索引...", timestamp=now-timedelta(hours=2)),
            ChatMessage(id="chat_009", agent_id="office_004", role="user", content="供应链目前有什么问题？", timestamp=now-timedelta(hours=1)),
            ChatMessage(id="chat_010", agent_id="office_004", role="agent", content="主要问题在于库存周转率偏低和供应商集中度高...", timestamp=now-timedelta(hours=1)),
            ChatMessage(id="chat_011", agent_id="office_001", role="user", content="生成一份调研报告", timestamp=now-timedelta(minutes=30)),
            ChatMessage(id="chat_012", agent_id="office_001", role="agent", content="已为您生成新能源汽车市场调研报告，请到成果中心查看。", timestamp=now-timedelta(minutes=30)),
        ]
        db.add_all(chats)

        # ===== 8. 系统事件（10 条）=====
        events = [
            EventLog(id="event_001", type="agent", title="林墨加入办公室", description="市场分析师 林墨 已雇佣入职", timestamp=now-timedelta(days=30)),
            EventLog(id="event_002", type="agent", title="陈雪加入办公室", description="财务顾问 陈雪 已雇佣入职", timestamp=now-timedelta(days=25)),
            EventLog(id="event_003", type="agent", title="赵磊加入办公室", description="全栈工程师 赵磊 已雇佣入职", timestamp=now-timedelta(days=20)),
            EventLog(id="event_004", type="agent", title="王芳加入办公室", description="供应链专家 王芳 已雇佣入职", timestamp=now-timedelta(days=15)),
            EventLog(id="event_005", type="task", title="任务完成", description="林墨 完成了「新能源汽车市场调研」", timestamp=now-timedelta(days=4)),
            EventLog(id="event_006", type="task", title="任务完成", description="陈雪 完成了「Q3财务报表分析」", timestamp=now-timedelta(days=3)),
            EventLog(id="event_007", type="meeting", title="会议结束", description="「Q4战略规划讨论」已结束", timestamp=now-timedelta(days=1)),
            EventLog(id="event_008", type="task", title="任务失败", description="林墨 的「竞品功能对比」任务失败", timestamp=now-timedelta(days=2)),
            EventLog(id="event_009", type="task", title="任务开始", description="赵磊 开始执行「服务器架构优化」", timestamp=now-timedelta(hours=2)),
            EventLog(id="event_010", type="system", title="系统启动", description="Agent Office OS 已启动", timestamp=now),
        ]
        db.add_all(events)

        db.commit()
        print("[种子数据] 初始化完成：8 个市场Agent、4 个办公室Agent、6 条任务、1 条会议、8 条成果、12 条聊天、10 条事件")

    except Exception as e:
        db.rollback()
        print(f"[种子数据] 初始化失败: {e}")
    finally:
        db.close()
