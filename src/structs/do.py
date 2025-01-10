from typing import Any, Dict

from pydantic import BaseModel, Field


class DoingOutput(BaseModel):
    result: str = Field(description="the text output needed for completing the task")
    obstacles: str = Field(
        description="obstacles found during executing the task for further reference"
    )
