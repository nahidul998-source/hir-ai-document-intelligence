from abc import ABC, abstractmethod
from typing import Dict, Any

class IERPAdapter(ABC):
    @abstractmethod
    async def push_data(self, session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pushes approved review data to the ERP.
        Returns the structured response from the ERP.
        Raises an exception if the push fails.
        """
        pass
