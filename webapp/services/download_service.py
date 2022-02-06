
from typing import Callable, Dict, Union, List
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
            headers.update(additional_headers)
            headers.update(self.HEADERS)

            resp = await self.client.request(method, url, headers=headers)

            if resp.status_code == 200:
                return await func(self, resp, **kwargs)
            else:
                raise RuntimeError(f"response status code: {resp.status_code}")
        return wrapped
    return outter_wrapped


class DownloadService:

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7,ja;q=0.6,zh-CN;q=0.5'
    }    

    def __init__(self, max_connections, max_keepalive_connections) -> None:
        limits = Limits(max_connections=max_connections, max_keepalive_connections=max_keepalive_connections)
        self.client = AsyncClient(limits=limits, timeout=5, verify=False)
    
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

    