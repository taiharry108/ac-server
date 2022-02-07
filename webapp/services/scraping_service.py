
import dataclasses
from webapp.services.abstract_manga_site_scraping_service import AbstractMangaSiteScrapingService

from webapp.services.download_service import DownloadService

@dataclasses.dataclass
class ScrapingService:
    download_service: DownloadService
    manga_site_scraping_service: AbstractMangaSiteScrapingService