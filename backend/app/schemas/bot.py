from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class BotBase(BaseModel):
    """Base bot schema with common attributes."""
    bot_name: str = Field(..., min_length=1, max_length=255, description="Name of the bot")
    description: Optional[str] = Field(None, max_length=5000, description="Bot description")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="Bot capabilities")
    endpoint: Optional[str] = Field(None, max_length=512, description="Bot endpoint URL")
    version: Optional[str] = Field(None, max_length=50, description="Bot version")


class BotCreate(BotBase):
    """Schema for creating a new bot."""
    bot_id: str = Field(..., min_length=1, max_length=255, description="Unique bot identifier")
    owner_id: UUID = Field(..., description="UUID of the bot owner")


class BotUpdate(BaseModel):
    """Schema for updating an existing bot."""
    bot_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    capabilities: Optional[Dict[str, Any]] = None
    endpoint: Optional[str] = Field(None, max_length=512)
    version: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, pattern="^(online|offline|busy|error)$")


class BotHeartbeat(BaseModel):
    """Schema for bot heartbeat reporting."""
    status: str = Field(..., pattern="^(online|offline|busy|error)$", description="Current bot status")
    capabilities: Optional[Dict[str, Any]] = None
    version: Optional[str] = Field(None, max_length=50)


class BotResponse(BotBase):
    """Schema for bot response data."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Internal UUID")
    bot_id: str = Field(..., description="Unique bot identifier")
    owner_id: UUID = Field(..., description="UUID of the bot owner")
    status: str = Field(..., description="Current bot status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_heartbeat_at: Optional[datetime] = Field(None, description="Last heartbeat timestamp")


class BotListResponse(BaseModel):
    """Schema for paginated bot list response."""
    items: List[BotResponse] = Field(..., description="List of bots")
    total: int = Field(..., description="Total number of bots")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")


class BotFilterParams(BaseModel):
    """Schema for bot list filter parameters."""
    status: Optional[str] = Field(None, description="Filter by status")
    owner_id: Optional[UUID] = Field(None, description="Filter by owner")
    search: Optional[str] = Field(None, description="Search in bot_name and description")
