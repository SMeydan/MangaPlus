from datetime import date
from typing import Optional
from pydantic import BaseModel


class User(BaseModel):
    user_id: str
    name: str
    surname: str
    email: str
    password: str
    age: int
    country: str
    user_created_time: date = date.today()
    is_active: bool = True

class UpdatedUser(BaseModel):
    name: Optional[str]
    surname: Optional[str]
    email: Optional[str]
    password: Optional[str]
    age: Optional[int]
    country: Optional[str]
