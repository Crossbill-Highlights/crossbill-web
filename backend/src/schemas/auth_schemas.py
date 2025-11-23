from pydantic import BaseModel, Field


class LoginResponse(BaseModel):
    access_token: str = Field(..., description="Access token")
    token_type: str = Field(..., description="Token type, e.g., 'bearer'")
