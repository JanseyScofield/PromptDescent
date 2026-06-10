from pydantic import BaseModel, Field

class PromptUpdate(BaseModel):
    new_prompt: str = Field(description="The newly optimized prompt.")
