from pydantic import BaseModel, EmailStr, Field


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str = Field(min_length=10, max_length=2000)
    new_password: str = Field(min_length=8, max_length=72)


class ChangePasswordIn(BaseModel):
    current_password: str = Field(max_length=72)
    new_password: str = Field(min_length=8, max_length=72)
