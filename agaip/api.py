# agaip/api.py
import asyncio
import logging

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from agaip.agent_manager import AgentManager
from agaip.config import load_config
from agaip.db import init_db, close_db

app = FastAPI(
    title="Agaip - Super Power Agentic AI Framework",
    description="Endüstri standartlarında, optimize, asenkron, API odaklı ve çoklu dil entegrasyonuna uygun agentic AI framework’ü",
    version="2.0.0"
)

security = HTTPBearer()
logger = logging.getLogger("agaip")
logging.basicConfig(level=logging.INFO)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token != "gecerli_token":
        raise HTTPException(status_code=401, detail="Yetkisiz erişim.")
    return token

class TaskRequest(BaseModel):
    agent_id: str
    payload: dict

agent_manager = AgentManager()
config = load_config()

@app.on_event("startup")
async def startup_event():
    # Local veya sunucu ortamına göre veritabanı başlatılır
    await init_db()
    # Konfigürasyonda tanımlı agent’ler asenkron olarak kaydediliyor
    for agent_config in config.get("agents", []):
        agent_id = agent_config["id"]
        plugin_path = agent_config["plugin"]
        try:
            await agent_manager.register_agent(agent_id, plugin_path)
            logger.info(f"Agent '{agent_id}' başarıyla kaydedildi. Plugin: {plugin_path}")
        except Exception as e:
            logger.error(f"Agent '{agent_id}' kaydı başarısız. Plugin: {plugin_path}. Hata: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

@app.post("/agent/task", summary="Agent'e görev gönder", response_model=dict)
async def send_task(task: TaskRequest, token: str = Depends(verify_token)):
    result = await agent_manager.dispatch_task(task.agent_id, task.payload)
    return result

@app.get("/status/{agent_id}", summary="Agent durumunu sorgula", response_model=dict)
async def get_agent_status(agent_id: str, token: str = Depends(verify_token)):
    agent = agent_manager.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent bulunamadı.")
    return {"agent_id": agent_id, "status": agent.status}

@app.get("/tasks", summary="Tüm görevleri listele", response_model=list)
async def list_tasks(token: str = Depends(verify_token)):
    from agaip.models.task import Task
    tasks = await Task.all().values()
    return tasks

@app.get("/tasks/{task_id}", summary="Görev detayını sorgula", response_model=dict)
async def get_task(task_id: int, token: str = Depends(verify_token)):
    from agaip.models.task import Task
    task = await Task.get_or_none(id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı.")
    return task.to_dict()
