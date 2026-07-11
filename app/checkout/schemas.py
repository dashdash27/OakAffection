from pydantic import BaseModel, Field, EmailStr
from typing import Dict

# name - ФИО минимум 2 слова
# phone - +7 и 10 цифр
# email поля
# delivery.service - str, может пустая
# delivery.settlement.name - str > 1 симв
# delivery.point.address - str > 1 симв
# delivery.point.id - str > 1 симв
# delivery.price - int не пустой
# delivery_token > str > 10 симв
# days - str, может пустая
# client_total_amount - int не пустой

class ClientContactsSchema(BaseModel):
    name: str = Field(
        ..., 
        min_length=3, 
        max_length=150,
        pattern=r"^\s*[a-zA-Zа-яА-ЯёЁ]+(?:\s+[a-zA-Zа-яА-ЯёЁ]+)+\s*$"
    )
    phone: str = Field(..., min_length=12, max_length=12, pattern=r"^\+7\d{10}$", strip_whitespace=True)
    email: EmailStr

class SettlementSchema(BaseModel):
    name: str = Field(..., min_length=2)
    postal_code: str = Field(default="")

class PointSchema(BaseModel):
    address: str = Field(..., min_length=2)
    id: str = Field(..., min_length=2)

class DeliverySchema(BaseModel):
    service: str = Field(default="") 
    settlement: SettlementSchema
    point: PointSchema
    price: int = Field(..., ge=0)
    days: str = Field(default="")
    delivery_token: str = Field(..., min_length=11)

class OrderCreateSchema(BaseModel):
    client_total_amount: int = Field(..., ge=0)
    client_contacts: ClientContactsSchema
    delivery: DeliverySchema
    cart: Dict[str, int] = Field(..., min_length=1)