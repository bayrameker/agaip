# agaip/plugins/dummy_model.py
from agaip.plugins.base_model import BaseModelPlugin
import asyncio

class DummyModelPlugin(BaseModelPlugin):
    def __init__(self):
        self.model = None

    async def load_model(self) -> None:
        # Model yükleme simülasyonu
        await asyncio.sleep(0.1)
        self.model = "dummy_model_loaded"

    async def predict(self, input_data: dict) -> dict:
        # Asenkron simülasyon: tahmin işlemi
        await asyncio.sleep(0.1)
        return {
            "status": "success",
            "model": self.model,
            "input": input_data,
            "result": "dummy_prediction"
        }
