"""Feature flags module for centralized feature toggle management."""

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field

from src.config import get_settings


class FeatureFlags(BaseModel):
    """Pydantic model defining all feature flags in the application."""

    ai: bool = Field(..., description="Whether AI features are enabled")
    user_registrations: bool = Field(..., description="Whether user registration is enabled")


# Type alias for valid feature flag keys
FeatureFlagKey = Literal["ai", "user_registrations"]


def get_feature_flags() -> FeatureFlags:
    """
    Get current feature flags based on application configuration.

    Returns:
        FeatureFlags instance with current flag values
    """
    settings = get_settings()

    return FeatureFlags(
        ai=settings.ai_enabled,
        user_registrations=settings.ALLOW_USER_REGISTRATIONS,
    )


def get_feature_flag(key: FeatureFlagKey) -> bool:
    """
    Get the value of a specific feature flag.

    Args:
        key: The feature flag key to retrieve. Must be a valid FeatureFlagKey.

    Returns:
        Boolean value of the feature flag
    """
    flags = get_feature_flags()
    return getattr(flags, key)


def is_ai_enabled() -> bool:
    """Check if AI features are enabled."""
    return get_feature_flag("ai")


def is_user_registrations_enabled() -> bool:
    """Check if user registrations are enabled."""
    return get_feature_flag("user_registrations")
