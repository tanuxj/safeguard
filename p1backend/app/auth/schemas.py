from pydantic import BaseModel


class UserLoginData(BaseModel):
    email: str
    password: str


class UserSignupData(BaseModel):
    firstName: str
    lastName: str
    email: str
    password: str


class UserLoginResponse(BaseModel):
    message: str
