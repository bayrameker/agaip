"""
Dummy model plugin for testing purposes.
"""

import asyncio
import random
from typing import Any, Dict

from agaip.plugins.base import BasePlugin


class DummyModelPlugin(BasePlugin):
    """A dummy model that returns random responses for testing."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.name = "dummy_model"
        self.version = "1.0.0"
        self.description = "A dummy model plugin for testing and development"
        self.author = "Agaip Framework"
    
    async def load_model(self) -> None:
        """Simulate model loading."""
        print(f"Loading {self.name}...")
        await asyncio.sleep(1)  # Simulate loading time
        self.is_loaded = True
        print(f"{self.name} loaded successfully!")
    
    async def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a dummy prediction."""
        if not self.is_loaded:
            await self.load_model()
        
        # Simulate processing time
        processing_time = self.config.get("processing_time", random.uniform(0.1, 0.5))
        await asyncio.sleep(processing_time)
        
        # Generate dummy response
        responses = [
            "This is a dummy response.",
            "Hello from the dummy model!",
            "Random prediction: 42",
            "The answer is always 42.",
            "Dummy model says: Everything is awesome!"
        ]
        
        return {
            "response": random.choice(responses),
            "confidence": random.uniform(0.7, 0.99),
            "model": self.name,
            "version": self.version,
            "input_data": data,
            "processing_time": processing_time
        }
