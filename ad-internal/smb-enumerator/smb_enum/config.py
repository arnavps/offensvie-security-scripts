"""
Configuration and validation for the SMB Enumerator.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator

class ScanConfig(BaseModel):
    """Configuration for an SMB enumeration scan."""
    
    # Target specification
    targets: List[str] = Field(description="List of IP addresses, CIDRs, or hostnames to scan")
    
    # Authentication
    domain: str = Field(default="", description="Active Directory domain (leave empty for local/workgroup)")
    username: str = Field(default="", description="Username for authentication (empty for Null session)")
    password: str = Field(default="", description="Password for authentication")
    hash: str = Field(default="", description="NTLM hash for authentication (format: LM:NT or NT)")
    
    # Connection parameters
    port: int = Field(default=445, description="SMB Port (usually 445)")
    timeout: float = Field(default=3.0, description="Connection timeout in seconds")
    threads: int = Field(default=10, description="Number of concurrent threads", ge=1, le=100)
    
    # Output and behavior
    json_out: Optional[str] = Field(default=None, description="Path to export results as JSON")
    check_write: bool = Field(default=False, description="Attempt to verify write access (creates/deletes a temp file)")
    
    @model_validator(mode='after')
    def validate_auth(self) -> 'ScanConfig':
        """Ensure either password or hash is provided if a username is given."""
        if self.username and not (self.password or self.hash):
            raise ValueError("Authentication requires either a password or a hash when a username is specified.")
        
        # If no username is provided, we default to a Null session (anonymous)
        # which is perfectly valid for enumeration, so we don't enforce username to be present.
        return self
    
    @property
    def is_null_session(self) -> bool:
        """Returns True if no username is provided (Null Session)."""
        return not bool(self.username)
