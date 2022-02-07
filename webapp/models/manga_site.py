from pydantic import BaseModel, HttpUrl

class MangaSite(BaseModel):
    id: int
    name: str
    url: HttpUrl

    class Config:
        orm_mode = True
