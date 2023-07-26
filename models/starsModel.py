from datetime import date
from typing import Optional
from pydantic import BaseModel


class Stars(BaseModel):
    manga_id: Optional[str]
    user_id: Optional[str]
    stars_id: Optional[str]
    stars: float
    update_time: date
    is_active: bool = True
