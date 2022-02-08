import abc
import dataclasses
from pathlib import Path
from typing import Generator, List


from webapp.models.chapter import Chapter
from webapp.models.manga import Manga

from webapp.models.manga_site import MangaSite
from webapp.services.async_service import AsyncService

from .download_service import DownloadService

import hashlib

@dataclasses.dataclass
class AbstractMangaSiteScrapingService(metaclass=abc.ABCMeta):
    download_service: DownloadService
    async_service: AsyncService
    site: MangaSite

    @abc.abstractmethod
    async def search_manga(self, keyword: str) -> List[Manga]:
        """Search manga with keyword, return a list of manga"""
        return []

    @abc.abstractmethod
    async def get_index_page(self, manga: Manga) -> Manga:
        """Get index page of manga, return a manga with chapters"""
        return

    @abc.abstractmethod
    async def get_page_urls(self, chapter: Chapter) -> List[str]:
        """Get all the urls of a chaper, return a list of strings"""
        return []

    def create_img_name(self, manga: Manga, chapter: Chapter = None, idx: int = None) -> str:
        name = self.site.name + manga.name
        if chapter:
            name += chapter.title
        if idx is not None:
            name += str(idx)

        hash_object = hashlib.md5(name.encode())
        return hash_object.hexdigest()

    async def download_chapter(self, manga: Manga, chapter: Chapter) -> Generator:
        img_urls = await self.get_page_urls(chapter)
        download_path = Path(self.site.name) / manga.name / chapter.title

        work_list = [{
            "url": img_url,
            "filename": self.create_img_name(manga, chapter, idx),
            "idx": idx
        } for idx, img_url in enumerate(img_urls)]

        async for result_dict in self.async_service.work(
                work_list, self.download_service.download_img, download_path=download_path):
            yield result_dict
        




