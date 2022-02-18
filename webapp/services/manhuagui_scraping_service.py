import dataclasses
from typing import List
from webapp.models.chapter import Chapter

from webapp.models.manga import Manga

from webapp.models.site import Site

from webapp.services.abstract_manga_site_scraping_service import AbstractMangaSiteScrapingService


@dataclasses.dataclass
class ManhuaguiScrapingService(AbstractMangaSiteScrapingService):
    site: Site = Site(
        id=0, name="manhuagui", url="https://www.manhuagui.com/")
    
    async def search_manga(self, keyword: str) -> List[Manga]:
        """Search manga with keyword, return a list of manga"""
        return [Manga(name="test", url="https://test.com")]
    
    async def get_index_page(self, page: str) -> Manga:
        """Get index page of manga, return a manga with chapters"""
        return Manga(name="test", url="https://test.com")

    async def get_page_urls(self, chapter: Chapter) -> List[str]:
        """Get all the urls of a chaper, return a list of strings"""
        return []
