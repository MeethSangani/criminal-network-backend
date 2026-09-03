from typing import List, Optional
from pydantic import BaseModel

class NodeSchema(BaseModel):
    id: str
    label: str
    type: str

class EdgeSchema(BaseModel):
    source: str
    target: str
    type: str
    timestamp: Optional[str] = None

class NetworkGraphData(BaseModel):
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]

class NetworkResponse(BaseModel):
    success: bool = True
    data: NetworkGraphData

class PathFindingData(BaseModel):
    hops: int
    nodes: List[str]
    edges: List[EdgeSchema]
    evidence_ids: List[str] = []

class PathFindingResponse(BaseModel):
    success: bool = True
    data: PathFindingData
