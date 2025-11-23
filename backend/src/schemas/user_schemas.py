from pydantic import BaseModel, Field


class UserBase(BaseModel):
    id: int = Field(..., description="User id")
    name: str = Field(..., min_length=1, max_length=100, description="User name")


class UserDetailsResponse(UserBase):
    """Schema for returning user details."""
