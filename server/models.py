from decimal import Decimal
from pydantic import BaseModel, Field


class TransferRequest(BaseModel):
    tx_id: str = Field(..., min_length=1)
    origin_account: str = Field(..., min_length=1)
    destination_account: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    timestamp: int = Field(..., gt=0)


class TransferResponse(BaseModel):
    status: str
    message: str
    tx_id: str

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


class RegisterResponse(BaseModel):
    id: int
    username: str
    message: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    id: int
    username: str