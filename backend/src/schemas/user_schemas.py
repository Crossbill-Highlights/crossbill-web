from pydantic import BaseModel, Field


class UserBase(BaseModel):
    id: int = Field(..., description="User id")
    name: str = Field(..., min_length=1, max_length=100, description="User name")


class UserDetailsResponse(UserBase):
    """Schema for returning user details."""


class UserUpdateRequest(BaseModel):
    """Schema for updating user profile."""

    name: str | None = Field(None, min_length=1, max_length=100, description="New user name")
    current_password: str | None = Field(
        None, min_length=1, description="Current password (required when changing password)"
    )
    new_password: str | None = Field(
        None, min_length=8, description="New password (min 8 characters)"
    )


class UserRegisterRequest(BaseModel):
    """Schema for user registration."""

    username: str = Field(
        ..., min_length=1, max_length=100, description="Username for the new account"
    )
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
