
import asyncio
from pathlib import Path
from turtle import down
from typing import Callable, Dict, Union, List
import uuid
from bs4 import BeautifulSoup
from httpx import AsyncClient, Limits
from pydantic import HttpUrl
from functools import wraps
from httpx import Response


def request_resp(method: str = "GET"):
    def outter_wrapped(func: Callable) -> Callable:
        @wraps(func)
        async def wrapped(self, url: HttpUrl, additional_headers: Dict[str, str] = {}, **kwargs):
            headers = {}
            # headers.update(additional_headers)
            headers.update(self.headers)

            resp = await self.client.request(method, url, headers=headers)

            if resp.status_code == 200:
                return await func(self, resp, **kwargs)
            else:
                raise RuntimeError(f"response status code: {resp.status_code}")
        return wrapped
    return outter_wrapped


class DownloadService:
    """Handle all the http requests"""

    def __init__(self, max_connections: int, max_keepalive_connections: int, headers: Dict[str, str], download_dir: str) -> None:
        limits = Limits(max_connections=max_connections,
                        max_keepalive_connections=max_keepalive_connections)
        self.client = AsyncClient(limits=limits, timeout=5, verify=False)
        self.headers = headers
        self.download_dir = Path(download_dir)

    @request_resp("GET")
    async def get_json(self, resp: Response) -> Union[List, Dict]:
        """Make a get request and return with json"""
        return resp.json()

    @request_resp("GET")
    async def get_bytes(self, resp: Response) -> bytes:
        """Make a get request and return with bytes"""
        print(resp.content)
        return resp.content

    @request_resp("GET")
    async def get_byte_soup(self, resp: Response) -> BeautifulSoup:
        """Make a get request and return with BeautifulSoup"""
        return BeautifulSoup(resp.content, features="html.parser")

    @request_resp("GET")
    async def get_soup(self, resp: Response) -> BeautifulSoup:
        """Make a get request and return with BeautifulSoup"""
        return BeautifulSoup(resp.text, features="html.parser")

    def setup_download_path(self, download_path: Path = None) -> Path:
        dir_path = self.download_dir
        if download_path is not None:
            dir_path /= download_path
        dir_path.mkdir(exist_ok=True, parents=True)
        return dir_path

    def setup_file_path(self, content_type: str, dir_path: Path, filename: str = None) -> Path:
        if filename is None:
            filename = uuid.uuid4()
        file_path = dir_path / \
            f'{filename}.{content_type.split("/")[-1]}'
        return file_path

    @request_resp("GET")
    async def download_img(self, resp: Response, download_path: Path = None, filename: str = None, **kwargs) -> Dict:
        b = resp.content

        content_type = resp.headers['content-type']
        if not content_type.startswith('image'):
            raise RuntimeError("Response is not an image")

        dir_path = self.setup_download_path(download_path)
        file_path = self.setup_file_path(content_type, dir_path, filename)
        with open(file_path, 'wb') as img_f:
            img_f.write(b)
        result = {"pic_path": str(file_path)}
        result.update(kwargs)
        return result
