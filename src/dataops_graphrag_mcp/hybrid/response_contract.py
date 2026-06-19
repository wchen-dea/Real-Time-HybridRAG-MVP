from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    source_type: str
    source_name: str
    source_uri: str | None = None
    excerpt: str
    confidence: float = Field(ge=0.0, le=1.0)


class GraphPathItem(BaseModel):
    source_node: str
    relationship: str
    target_node: str
