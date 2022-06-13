from pydantic import BaseModel
# from typing import List, Optional

class UserBase(BaseModel):
    username: str
    hash_pass: str
    
class User(UserBase):
    id: int
    role: str
    class Config:
        orm_mode = True

class UserCreate(UserBase):
    pass
