"""Pydantic schemas for HighlightTag API request/response validation."""

from pydantic import BaseModel, Field


class HighlightTagBase(BaseModel):
    """Base schema for HighlightTag."""

    name: str = Field(..., min_length=1, max_length=100, description="Tag name")


class HighlightTag(HighlightTagBase):
    """Schema for HighlightTag response."""

    id: int
    book_id: int
    tag_group_id: int | None = None

    model_config = {"from_attributes": True}


class HighlightTagInBook(BaseModel):
    """Minimal highlight tag schema for book responses."""

    id: int
    name: str
    tag_group_id: int | None = None

    model_config = {"from_attributes": True}


class HighlightTagCreateRequest(BaseModel):
    """Schema for creating a new highlight tag."""

    name: str = Field(..., min_length=1, max_length=100, description="Tag name")


class HighlightTagsResponse(BaseModel):
    """Schema for list of highlight tags response."""

    tags: list[HighlightTag] = Field(..., description="List of highlight tags")


class HighlightTagAssociationRequest(BaseModel):
    """Schema for associating a tag with a highlight."""

    tag_id: int | None = Field(None, description="ID of existing tag to associate")
    name: str | None = Field(
        None, min_length=1, max_length=100, description="Name of tag to create/associate"
    )


class HighlightTagUpdateRequest(BaseModel):
    """Schema for updating an existing highlight tag."""

    name: str | None = Field(None, min_length=1, max_length=100, description="Tag name")
    tag_group_id: int | None = Field(None, description="ID of tag group to associate with")


class HighlightTagGroupBase(BaseModel):
    """Base schema for HighlightTagGroup."""

    name: str = Field(..., min_length=1, max_length=100, description="Tag group name")


class HighlightTagGroup(HighlightTagGroupBase):
    """Schema for HighlightTagGroup response."""

    id: int
    book_id: int

    model_config = {"from_attributes": True}


class HighlightTagGroupInBook(BaseModel):
    """Minimal highlight tag group schema for book responses."""

    id: int
    name: str

    model_config = {"from_attributes": True}


class HighlightTagGroupCreateRequest(BaseModel):
    """Schema for creating or updating a highlight tag group."""

    id: int | None = Field(None, description="ID of existing tag group to update (optional)")
    book_id: int = Field(..., description="ID of the book this tag group belongs to")
    name: str = Field(..., min_length=1, max_length=100, description="Tag group name")


class HighlightTagGroupsResponse(BaseModel):
    """Schema for list of highlight tag groups response."""

    tag_groups: list[HighlightTagGroup] = Field(..., description="List of highlight tag groups")
