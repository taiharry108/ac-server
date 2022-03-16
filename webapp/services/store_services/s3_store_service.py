import dataclasses
from functools import wraps
import hashlib
from logging import getLogger
from time import mktime
from typing import AsyncIterator, Dict

from webapp.services.store_services.abstract_store_service import AbstractStoreService

from botocore import session, exceptions
import asyncio
from smart_open import open

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


def run_in_executor(f):
    @wraps(f)
    def inner(*args, **kwargs):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, lambda: f(*args, **kwargs))

    return inner


@dataclasses.dataclass
class S3StoreService(AbstractStoreService):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region_name: str
    aws_use_ssl: bool
    aws_verify: bool
    uri: str

    def __post_init__(self):
        s = session.get_session()
        self.s3_client = s.create_client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region_name,
            use_ssl=self.aws_use_ssl,
            verify=self.aws_verify
        )
        if not self.uri.startswith("s3://"):
            raise ValueError(
                f"Incorrect URI scheme in {self.uri}, expected 's3'")
        self.bucket, self.prefix = self.uri[5:].split('/', 1)

    @run_in_executor
    def get_boto_key(self, path: str) -> Dict:
        key_name = f'{self.prefix}{path}'
        try:
            return self.s3_client.head_object(Bucket=self.bucket, Key=key_name)
        except exceptions.ClientError:
            return {}

    async def persist_file(self, path: str, async_iter: AsyncIterator[bytes] = None, meta: Dict = None) -> str:
        """Upload file to S3 storage"""
        key_name = f'{self.prefix}{path}'
        url = f's3://{self.bucket}/{key_name}'
        logger.info(f"{key_name=}, {url=}")

        with open(url, 'wb', transport_params={'client': self.s3_client, 'min_part_size': 5 * 1024**2}) as f:
            async for data in async_iter:
                await run_in_executor(f.write)(data)
        
        logger.info('finished saving file')
        return path

    async def stat_file(self, path: str) -> Dict[str, str]:
        """Return stat of a file"""

        boto_key = await self.get_boto_key(path)

        checksum = boto_key['ETag'].strip('"')
        last_modified = boto_key['LastModified']
        modified_stamp = mktime(last_modified.timetuple())
        return {'checksum': checksum, 'last_modified': modified_stamp}

    async def file_exists(self, path: str) -> bool:
        boto_key = await self.get_boto_key(path)
        return len(boto_key) != 0
