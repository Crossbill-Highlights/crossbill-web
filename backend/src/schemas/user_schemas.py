from pydantic import BaseModel, Field


class UserBase(BaseModel):
    id: int = Field(..., description="User id")
    email: str = Field(..., min_length=1, max_length=100, description="User email")


class UserDetailsResponse(UserBase):
    """Schema for returning user details."""


class UserUpdateRequest(BaseModel):
    """Schema for updating user profile."""

    email: str | None = Field(None, min_length=1, max_length=100, description="New user email")
    current_password: str | None = Field(
        None, min_length=1, description="Current password (required when changing password)"
    )
    new_password: str | None = Field(
        None, min_length=8, description="New password (min 8 characters)"
    )


class UserRegisterRequest(BaseModel):
    """Schema for user registration."""

    email: str = Field(..., min_length=1, max_length=100, description="Email for the new account")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
