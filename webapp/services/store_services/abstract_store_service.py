import abc
import dataclasses
from typing import Dict


@dataclasses.dataclass
class AbstractStoreService(metaclass=abc.ABCMeta):
    base_dir: str

    @abc.abstractclassmethod
    def persist_file(self, path: str, data: bytes, meta: Dict = None) -> str:
        """Save a file to store return path"""
        return ""

    @abc.abstractclassmethod
    def stat_file(self, path) -> Dict[str, str]:
        """Return stat of a file"""
        return {}