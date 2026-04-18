from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class AffectedPackage(BaseModel):
    ecosystem: str
    name: str
    versions_affected: List[str]
    fixed_version: Optional[str] = None


class CveRecord(BaseModel):
    cve_id: str
    source: str
    published_at: datetime
    cvss_score: float
    affected_packages: List[AffectedPackage]
    description: str
    raw_data: Optional[Dict[str, Any]] = None


class DependencyResolutionMessage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    cve_id: str
    affected_package_ecosystem: str
    affected_package_name: str
    resolutions_found: int
    status: str
