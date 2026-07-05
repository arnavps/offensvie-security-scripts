from pydantic import BaseModel, Field
from typing import List, Optional

class Service(BaseModel):
    port_id: int
    protocol: str = "tcp"
    state: str
    name: Optional[str] = None
    product: Optional[str] = None
    version: Optional[str] = None
    
    @property
    def is_cleartext(self) -> bool:
        """Enrichment property to flag risky cleartext protocols."""
        return self.name in ["ftp", "telnet", "http"]

class Host(BaseModel):
    ip_address: str
    status: str
    hostnames: List[str] = Field(default_factory=list)
    services: List[Service] = Field(default_factory=list)
