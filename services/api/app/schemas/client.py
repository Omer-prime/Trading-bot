from pydantic import BaseModel, EmailStr


class ClientBase(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None
    status: str = "active"


class ClientCreate(ClientBase):
    pass


class ClientRead(ClientBase):
    id: int

    class Config:
        from_attributes = True
