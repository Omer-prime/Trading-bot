from pydantic import BaseModel, EmailStr, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool