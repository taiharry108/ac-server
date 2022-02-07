from fastapi import APIRouter, Depends
from webapp.containers import Container
from webapp.services.abstract_manga_site_scraping_service import AbstractMangaSiteScrapingService

from dependency_injector.wiring import inject, Provider, Provide

router = APIRouter()

@router.get("/test")
@inject
def test(service=Depends(Provide[Container.download_service])):
    print(service)
    
    return {"status": 200}
