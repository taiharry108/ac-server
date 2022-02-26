import dataclasses
import hashlib
from logging import getLogger
from pathlib import Path
from typing import AsyncIterator, Dict

from webapp.services.store_services.abstract_store_service import AbstractStoreService


logger = getLogger(__name__)


def md5sum(file):
    """Calculate the md5 checksum of a file-like object without reading its
    whole content in memory.
    >>> from io import BytesIO
    >>> md5sum(BytesIO(b'file content to hash'))
    '784406af91dd5a54fbb9c84c2236595a'
    """
    m = hashlib.md5()
    while True:
        d = file.read(8096)
        if not d:
            break
        m.update(d)
    return m.hexdigest()


@dataclasses.dataclass
class FSStoreService(AbstractStoreService):
    base_dir: str

    def get_filesystem_path(self, path: str):
        return Path(self.base_dir) / path

    async def persist_file(self, path: str, async_iter: AsyncIterator[bytes] = None, meta: Dict = None) -> str:
        """Save a file to store return path"""
        absolute_path = self.get_filesystem_path(path)
        absolute_path.parent.mkdir(exist_ok=True, parents=True)
        if async_iter is not None:
            with open(absolute_path, "wb") as f:
                async for chunk in async_iter:
                    f.write(chunk)
        return str(path)

    async def stat_file(self, path: str) -> Dict[str, str]:
        """Return stat of a file"""
        absolute_path = self.get_filesystem_path(path)
        try:
            last_modified = absolute_path.lstat().st_mtime
        except Exception as ex:
            logger.error(ex)
            return {}

        with open(absolute_path, 'rb') as f:
            checksum = md5sum(f)

        return {'last_modified': last_modified, 'checksum': checksum}
    
    async def file_exists(self, path: str) -> bool:
        """Return True if a file with a given path exists"""
        absolute_path = self.get_filesystem_path(path)
        return absolute_path.exists()

