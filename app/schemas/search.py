from typing import List, Optional
from pydantic import BaseModel

class SearchResultItem(BaseModel):
    id: str
    type: str  # PERSON, ORGANIZATION, LOCATION, VEHICLE, PHONE, CASE, BANK_ACCOUNT
    name: str
    matching_field: Optional[str] = None

class SearchData(BaseModel):
    results: List[SearchResultItem]

class SearchResponse(BaseModel):
    success: bool = True
    data: SearchData
