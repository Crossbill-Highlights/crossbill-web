from pydantic import BaseModel, Field


class AppSettingsResponse(BaseModel):
    """Schema for returning public application settings."""

    allow_user_registrations: bool = Field(..., description="Whether user registration is enabled")
    ai_features: bool = Field(..., description="Whether AI features are enabled")
