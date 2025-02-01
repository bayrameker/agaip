# agaip/agents/agent.py
import asyncio
from typing import Any, Dict

class Agent:
    def __init__(self, agent_id: str, model_plugin):
        self.agent_id = agent_id
        self.model_plugin = model_plugin  # Dinamik plugin (model/agent) nesnesi
        self.status = "idle"

    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        self.status = "processing"
        if asyncio.iscoroutinefunction(self.model_plugin.predict):
            result = await self.model_plugin.predict(task_data)
        else:
            result = await asyncio.to_thread(self.model_plugin.predict, task_data)
        self.status = "idle"
        return result
