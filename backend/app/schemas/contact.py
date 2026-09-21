from datetime import date, datetime
from typing import Annotated, List, Literal, Optional

from pydantic import BaseModel, Field

ContactType = Literal["personal", "needed", "spam", "other"]


class ContactCreate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    telegram_id: Optional[str] = Field(None, max_length=100)
    telegram_username: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    contact_type: ContactType = "other"
    birthday: Optional[date] = None
    is_known: Optional[bool] = None
    is_favorite: Optional[bool] = None
    folder_id: Optional[int] = None


class ContactUpdate(BaseModel):
    name: Annotated[Optional[str], Field(max_length=255)] = None
    phone: Annotated[Optional[str], Field(max_length=50)] = None
    email: Annotated[Optional[str], Field(max_length=255)] = None
    telegram_id: Annotated[Optional[str], Field(max_length=100)] = None
    telegram_username: Annotated[Optional[str], Field(max_length=100)] = None
    is_known: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_blocked: Optional[bool] = None
    contact_type: Optional[ContactType] = None
    birthday: Optional[date] = None
    folder_id: Optional[int] = None
    notes: Optional[str] = None


class ContactResponse(BaseModel):
    id: int
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram_id: Optional[str] = None
    telegram_username: Optional[str] = None
    is_known: bool = False
    is_favorite: bool = False
    is_blocked: bool = False
    contact_type: ContactType = "other"
    birthday: Optional[date] = None
    notes: Optional[str] = None
    channel_types: List[str] = []
    folder_id: Optional[int] = None
    message_count: int = 0
    task_count: int = 0
    last_message_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MergeContactsRequest(BaseModel):
    primary_id: int
    secondary_id: int


class BulkMergeRequest(BaseModel):
    primary_id: int
    secondary_ids: List[int]


class BulkIdsRequest(BaseModel):
    ids: List[int]


class BulkUpdateRequest(BaseModel):
    ids: List[int]
    is_known: Optional[bool] = None
    folder_id: Optional[int] = None
    is_favorite: Optional[bool] = None
    contact_type: Optional[ContactType] = None


class DuplicateGroup(BaseModel):
    contacts: List[ContactResponse]
    reason: str


class TimelineEvent(BaseModel):
    type: str
    title: str
    subtitle: str
    created_at: Optional[datetime] = None
    link: Optional[str] = None


class NoteCreate(BaseModel):
    content: str = Field(min_length=1)
    author: Optional[str] = None


class NoteResponse(BaseModel):
    id: int
    content: str
    author: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
