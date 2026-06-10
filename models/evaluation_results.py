from pydantic import BaseModel, Field

class EvaluationResult(BaseModel):
    error_score: float = Field(description="Error score between 0.0 (perfect match) and 1.0 (completely wrong).")
    feedback: str = Field(description="Detailed textual feedback on what the current extraction missed or hallucinated.")
