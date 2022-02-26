import abc
import dataclasses
from typing import AsyncIterator, Dict
from httpx import Response

@dataclasses.dataclass
class AbstractStoreService(metaclass=abc.ABCMeta):
    base_dir: str

    @abc.abstractmethod
    async def persist_file(self, path: str, async_iter: AsyncIterator[bytes] = None, meta: Dict = None) -> str:
        """Save a file to store return path"""
        return ""

    @abc.abstractmethod
    async def stat_file(self, path) -> Dict[str, str]:
        """Return stat of a file"""
        return {}
    
    @abc.abstractmethod
    async def file_exists(self, path: str) -> bool:
        return False