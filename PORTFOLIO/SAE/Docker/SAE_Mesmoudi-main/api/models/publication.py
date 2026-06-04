from pydantic import BaseModel
from typing import Optional

class Publication(BaseModel):
    titre: str
    annee: int
    type: str  # "journal" ou "conference"
    venue: Optional[str] = None
    journal: Optional[str] = None
    rang_core: Optional[str] = None
    quartile: Optional[str] = None
    sjr: Optional[float] = None
