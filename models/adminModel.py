from typing import Optional
from pydantic import BaseModel
from redis_om import get_redis_connection, HashModel

class Admin(HashModel):
    admin_id: str
    name: str
    surname: str
    email: str
    password: str
    is_active: bool = True

class UpdateAdmin(BaseModel):
    name: Optional[str]
    surname: Optional[str]
    email: Optional[str]
    password: Optional[str]  