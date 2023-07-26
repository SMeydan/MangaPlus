from pydantic import BaseModel


class Category(BaseModel):
    category_id: int
    subcategory_id: int
    age_restriction: int
    description: str
    is_active: bool = True


class SubCategory(BaseModel):
    subcategory_id: int
    category_id: int
    age_restriction: int
    description: str
    has_child: bool
    is_active: bool = True