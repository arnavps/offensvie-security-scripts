"""
Config Module
Defines the data models and configuration state for the brute forcer.
Uses Pydantic for strict validation.
"""
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Optional

class Config(BaseModel):
    target_url: HttpUrl
    wordlist_path: str
    extensions: List[str] = Field(default_factory=list)
    threads: int = Field(default=50, ge=1, le=500)
    timeout: int = Field(default=10, ge=1)
    retries: int = Field(default=3, ge=0)
    user_agent: str = Field(default="DirBruter/1.0 (Professional VAPT Tool)")
    output_file: Optional[str] = None
    allow_redirects: bool = Field(default=False)
    
    @validator('extensions', pre=True)
    def parse_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() if ext.startswith('.') else f".{ext.strip()}" for ext in v.split(',') if ext.strip()]
        return v
