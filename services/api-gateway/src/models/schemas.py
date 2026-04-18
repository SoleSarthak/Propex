from pydantic import BaseModel
from typing import List, Optional

class AffectedRepositoryResponse(BaseModel):
    id: int
    cve_id: str
    repository_url: str
    target_package: str
    dependency_depth: int
    context_type: str
    popularity_stars: int
    download_count: int
    propex_score: float
    maintainer_status: str

    class Config:
        from_attributes = True

class MaintainerStatusUpdate(BaseModel):
    status: str
