from fastapi import APIRouter, Depends
from webapp.containers import Container

from webapp.services.download_service import DownloadService
from dependency_injector.wiring import inject, Provide

router = APIRouter()

@router.get("/test")
@inject
def test(download_service: DownloadService = Depends(Provide[Container.download_service])):
    return download_service.HEADERS
