# agaip/plugins/base_model.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseModelPlugin(ABC):
    @abstractmethod
    async def load_model(self) -> None:
        """
        Modelin asenkron olarak yüklenmesi ve belleğe alınması.
        """
        pass

    @abstractmethod
    async def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asenkron olarak input verisine göre tahmin üretir.
        """
        pass
