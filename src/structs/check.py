from typing import List, Optional

from pydantic import BaseModel, Field


class CheckingOutput(BaseModel):
    success: bool = Field(
        description="whether the task was completed successfully ('passed') or needs to re-run ('failed')"
    )
    comments: str = Field(
        description="concise feedback on why the task was considered successful or not"
    )
    suggestions: Optional[str] = Field(
        description="suggestions to take into account in a re-run if the task failed"
    )
