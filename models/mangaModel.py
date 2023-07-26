from datetime import date
from typing import Optional
from pydantic import BaseModel
from redis_om import get_redis_connection, HashModel

class Manga(BaseModel):
    manga_id: str
    category_id: str
    subcategory_id: str
    name: str
    description: str
    pub_link: str
    publish_time: date
    price: float
    is_active: bool = True

class MangaBase(BaseModel):
    manga_id: str
    category_id: str
    subcategory_id: str
    name: str
    description: str
    price: float
    pub_link: Optional[str]
    publish_time: str

class UpdateManga(BaseModel):
    manga_id: Optional[str]
    category_id: Optional[str]
    subcategory_id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    publish_time: Optional[date]
    price: Optional[float]
    is_active: Optional[bool]
