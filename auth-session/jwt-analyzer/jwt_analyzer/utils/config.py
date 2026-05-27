"""
Configuration management.
Loads settings from a YAML file to make the tool extensible.
"""
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List

class AnalyzerConfig(BaseModel):
    sensitive_keys: List[str] = Field(default_factory=list)
    weak_algorithms: List[str] = Field(default_factory=list)

def load_config(config_path: str = "config/settings.yaml") -> AnalyzerConfig:
    """
    Loads configuration from a YAML file and validates it with Pydantic.
    """
    path = Path(config_path)
    if not path.exists():
        # Fallback to defaults if no config file is found
        return AnalyzerConfig(
            sensitive_keys=["password", "secret", "token", "ssn", "is_admin", "role", "uid", "email"],
            weak_algorithms=["none", "None", "NONE"]
        )
        
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    return AnalyzerConfig(**(data or {}))
