from pydantic import BaseModel, Field

from src.feature_flags import FeatureFlags


class AppSettingsResponse(BaseModel):
    """Schema for returning public application settings."""

    allow_user_registrations: bool = Field(..., description="Whether user registration is enabled")
    ai_features: bool = Field(..., description="Whether AI features are enabled")
    feature_flags: FeatureFlags = Field(..., description="All feature flags")
