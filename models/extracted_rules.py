from typing import List
from pydantic import BaseModel, Field

class ExtractedRules(BaseModel):
    id: str = Field(description="id of the file being extracted")
    pdf: str = Field(description="name of the process being extracted.")
    documents_needed: List[str] = Field(description="List of required documents to start the process.")
    information_needed: List[str] = Field(description="List of specific information/data required to start the process.")
