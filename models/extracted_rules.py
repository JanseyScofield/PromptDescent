from typing import List
from pydantic import BaseModel, Field

class ExtractedRules(BaseModel):
    documents_needed: List[str] = Field(description="List of required documents to start the process.")
    information_needed: List[str] = Field(description="List of specific information/data required to start the process.")
