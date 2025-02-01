# agaip/agent_manager.py
from typing import Dict
from agaip.agents.agent import Agent
from agaip.utils.plugin_loader import load_plugin
from agaip.models.task import Task  # Tortoise ORM modeli

class AgentManager:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}

    async def register_agent(self, agent_id: str, plugin_path: str) -> None:
        plugin_class = load_plugin(plugin_path)
        plugin_instance = plugin_class()
        await plugin_instance.load_model()
        agent = Agent(agent_id, plugin_instance)
        self.agents[agent_id] = agent

    async def dispatch_task(self, agent_id: str, task_data: Dict) -> Dict:
        if agent_id not in self.agents:
            return {"error": f"Agent '{agent_id}' bulunamadı."}
        # Görev veritabanına kaydediliyor (başlangıçta 'processing')
        task_record = await Task.create(
            agent_id=agent_id,
            payload=task_data,
            status="processing"
        )
        agent = self.agents[agent_id]
        result = await agent.process_task(task_data)
        task_record.result = result
        task_record.status = "completed"
        await task_record.save()
        return result
