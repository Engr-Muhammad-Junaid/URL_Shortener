from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from datetime import datetime


# What the user sends us
class URLCreate(BaseModel):
    original_url: HttpUrl


# What we send back
class URLResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_url: str
    short_code: str
    clicks: int
    created_at: datetime

class URLPage(BaseModel):
    items: list[URLResponse]
    total: int
    page: int
    page_size: int
    pages: int


class CleanupRequest(BaseModel):
    older_than_days: int = Field(default=30, ge=1, le=3650)
