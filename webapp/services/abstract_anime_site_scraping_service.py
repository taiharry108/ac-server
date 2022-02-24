import abc
import dataclasses
import hashlib
from logging import getLogger
from pathlib import Path
from typing import Generator, List


from webapp.models.anime import Anime
from webapp.models.episode import Episode
from webapp.models.site import Site
from webapp.services.async_service import AsyncService

from .download_service import DownloadService

logger = getLogger(__name__)
@dataclasses.dataclass
class AbstractAnimeSiteScrapingService(metaclass=abc.ABCMeta):
    download_service: DownloadService
    async_service: AsyncService
    site: Site

    @abc.abstractmethod
    async def search_anime(self, keyword: str) -> List[Anime]:
        """Search manga with keyword, return a list of manga"""

    @abc.abstractmethod
    async def get_index_page(self, anime: Anime) -> List[Episode]:
        """Get index page of anime, return a list of episodes"""

    @abc.abstractmethod
    async def get_video_url(self, ep: Episode) -> str:
        """Get all the urls of a chaper, return a list of strings"""
    
    def create_vid_name(self, anime: Anime, episode: Episode) -> str:
        name = self.site.name + anime.name
        if episode:
            name += episode.title

        hash_object = hashlib.md5(name.encode())
        return hash_object.hexdigest()
    
    async def download_episode(self, anime: Anime, episode: Episode) -> Generator:
        video_url = await self.get_video_url(episode)
        download_path = Path(self.site.name) / anime.name

        work_list = [{
            "url": video_url,
            "filename": self.create_vid_name(anime, episode),
        }]

        async for result_dict in self.async_service.work(
                work_list, self.download_service.download_vid, download_path=download_path):
            yield result_dict

   