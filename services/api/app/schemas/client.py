from pydantic import BaseModel, EmailStr, ConfigDict


class ClientBase(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None
    status: str = "active"


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None
    status: str | None = None


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
