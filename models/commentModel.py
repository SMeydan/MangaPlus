from datetime import date
from pydantic import BaseModel


class Comment(BaseModel):
    manga_id: str
    user_id: str
    comment_id: str
    description: str
    update_time: date
    is_active: bool = True