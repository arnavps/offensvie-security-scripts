import asyncio
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmailResult(BaseModel):
    """
    Represents a discovered email address.
    Strictly enforces types and performs basic validation.
    """
    model_config = ConfigDict(frozen=True)  # Makes it hashable for deduplication

    email: str = Field(..., description="The discovered email address")
    source: str = Field(..., description="The plugin/source where it was found (e.g., 'Bing', 'Hunter.io')")
    url: Optional[str] = Field(None, description="The specific URL where the email was located")

    @field_validator('email')
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Lowercases and strips whitespace."""
        return v.strip().lower()


class TargetDomain(BaseModel):
    """
    Represents the target domain.
    """
    domain: str = Field(..., description="The domain to harvest emails for")

    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v = v.strip().lower()
        if v.startswith("http://") or v.startswith("https://"):
            raise ValueError("Provide a domain name, not a URL (e.g., example.com)")
        if "/" in v:
            raise ValueError("Provide a clean domain name without paths")
        return v
