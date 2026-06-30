"""
Pydantic schemas for the Medical Telegram Warehouse API.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ Request Schemas ============

class SearchRequest(BaseModel):
    """Search messages request schema."""
    query: str = Field(..., min_length=1, description="Search keyword")
    channel: Optional[str] = Field(None, description="Filter by channel name")
    limit: int = Field(20, ge=1, le=100, description="Number of results to return")
    min_views: Optional[int] = Field(None, ge=0, description="Minimum view count filter")

    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class ChannelActivityRequest(BaseModel):
    """Channel activity request schema."""
    channel_name: str = Field(..., description="Channel name")
    days: int = Field(7, ge=1, le=30, description="Number of days to analyze")

    @validator('channel_name')
    def validate_channel_name(cls, v):
        if not v.strip():
            raise ValueError('Channel name cannot be empty')
        return v.strip()

class TopProductsRequest(BaseModel):
    """Top products request schema."""
    limit: int = Field(10, ge=1, le=50, description="Number of products to return")
    channel: Optional[str] = Field(None, description="Filter by channel name")


# ============ Response Schemas ============

class MessageResponse(BaseModel):
    """Message response schema."""
    message_id: int
    channel_name: str
    message_date: str
    message_text: str
    views: int
    forwards: int
    replies: int
    has_media: bool
    image_path: Optional[str] = None

class ChannelStats(BaseModel):
    """Channel statistics schema."""
    channel_name: str
    count: int

class MediaStats(BaseModel):
    """Media statistics schema."""
    with_media: int
    without_media: int

class StatsResponse(BaseModel):
    """Overall statistics response."""
    total_messages: int
    channels: List[ChannelStats]
    media_stats: MediaStats
    average_views: float
    last_updated: str

class ProductStats(BaseModel):
    """Product statistics schema."""
    product: str
    mentions: int
    avg_views: float
    avg_forwards: Optional[float] = None
    avg_replies: Optional[float] = None

class TopProductsResponse(BaseModel):
    """Top products response."""
    products: List[ProductStats]
    total_products_mentioned: int
    channel_filter: str
    limit: int

class DailyActivity(BaseModel):
    """Daily activity schema."""
    date: str
    messages: int
    avg_views: float
    with_media: Optional[int] = None
    engagement: Optional[float] = None

class ChannelSummary(BaseModel):
    """Channel summary schema."""
    total_messages: int
    avg_views: float
    max_views: int
    min_views: Optional[int] = None
    media_count: int
    media_percentage: float
    avg_forwards: Optional[float] = None
    avg_replies: Optional[float] = None

class ChannelActivityResponse(BaseModel):
    """Channel activity response."""
    channel: str
    period_days: int
    summary: ChannelSummary
    daily_activity: List[DailyActivity]
    top_messages: List[Dict[str, Any]]

class SearchResult(BaseModel):
    """Search result schema."""
    query: str
    total_results: int
    returned_results: int
    channel_filter: str
    min_views: Optional[str] = None
    results: List[Dict[str, Any]]

class VisualContentOverall(BaseModel):
    """Visual content overall stats."""
    with_media: int
    without_media: int
    media_percentage: float
    avg_views_with_media: float
    avg_views_without_media: float
    avg_forwards_with_media: Optional[float] = None
    avg_forwards_without_media: Optional[float] = None

class ChannelMediaStats(BaseModel):
    """Channel media statistics."""
    channel_name: str
    total_messages: int
    with_media: int
    media_percentage: float
    avg_views: float
    with_media_avg: Optional[float] = None
    without_media_avg: Optional[float] = None
    media_count: Optional[int] = None

class MediaImpact(BaseModel):
    """Media impact schema."""
    media_type: str
    avg_views: float
    avg_forwards: float
    avg_replies: float
    total_engagement: float

class VisualContentResponse(BaseModel):
    """Visual content statistics response."""
    overall: VisualContentOverall
    by_channel: List[ChannelMediaStats]
    media_impact: List[MediaImpact]
    insights: List[str]

class DailyTrend(BaseModel):
    """Daily trend schema."""
    date: str
    messages: int
    avg_views: float
    media_count: Optional[int] = None
    engagement: Optional[float] = None

class DailyTrendsResponse(BaseModel):
    """Daily trends response."""
    period_days: int
    channel_filter: str
    data: List[DailyTrend]
    trend_percentage: float
    total_messages: int
    avg_daily_messages: float
    peak_day: Optional[str] = None

class ImageDetectionCategory(BaseModel):
    """Image detection category schema."""
    category: str
    count: int
    total_images: Optional[int] = None
    medical_images: Optional[int] = None

class ImageAnalysisResponse(BaseModel):
    """Image analysis response."""
    total_images: int
    categories: List[ImageDetectionCategory]
    insights: Optional[List[str]] = None

class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
    status_code: int
    timestamp: str