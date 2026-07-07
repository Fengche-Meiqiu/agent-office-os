from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_ok():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "Agent Office OS"


def test_organization_api_is_removed():
    with TestClient(app) as client:
        response = client.get("/api/organization")

    assert response.status_code == 404


def test_v010_hermes_task_flow(monkeypatch):
    async def fake_discover_agents():
        return [
            {
                "id": "hermes_test_v010_agent",
                "name": "Nuwa Test Agent",
                "avatar": "",
                "title": "Meeting and task specialist",
                "platform": "Hermes",
                "skills": ["task execution", "meeting notes"],
                "tools": ["hermes-task"],
                "status": "ONLINE",
                "description": "Synthetic Hermes agent for V0.1.0 acceptance tests.",
            }
        ]

    async def fake_execute_task(agent_id: str, title: str, content: str):
        return {
            "task_id": "hermes_task_v010",
            "status": "completed",
            "result": f"Hermes completed {title}: {content}",
        }

    monkeypatch.setattr("app.api.marketplace.hermes_adapter.discover_agents", fake_discover_agents)
    monkeypatch.setattr("app.api.tasks.hermes_adapter.execute_task", fake_execute_task)

    with TestClient(app) as client:
        market_response = client.get("/api/marketplace/agents")
        assert market_response.status_code == 200
        agents = market_response.json()
        assert any(agent["id"] == "hermes_test_v010_agent" for agent in agents)

        hire_response = client.post("/api/marketplace/hire", json={"agentId": "hermes_test_v010_agent"})
        assert hire_response.status_code == 200
        office_agent_id = hire_response.json()["officeAgentId"]

        chat_response = client.post(
            f"/api/chat/{office_agent_id}/messages",
            json={"content": "/task Prepare V0.1.0 acceptance notes"},
        )
        assert chat_response.status_code == 200
        assert "Result has been saved to Outputs" in chat_response.json()["content"]

        tasks_response = client.get("/api/tasks")
        assert tasks_response.status_code == 200
        tasks = tasks_response.json()
        created_task = next(task for task in tasks if task["agentId"] == office_agent_id)
        assert created_task["status"] == "Completed"
        assert created_task["outputId"]

        outputs_response = client.get("/api/outputs")
        assert outputs_response.status_code == 200
        outputs = outputs_response.json()
        assert any(output["id"] == created_task["outputId"] for output in outputs)
