from typing import List, Optional

from pydantic import BaseModel, Field


class PlanningStep(BaseModel):
    step: str = Field(description="short description of the step (action) to take")
    details: str = Field(
        description="details of the step (action) to take in order to provider more context and being more precise"
    )
    expected_outcome: str = Field(
        description="details of the expected outcome, for being able to evaluate after its success"
    )


class PlanningOutput(BaseModel):
    next_steps: List[PlanningStep]
    feedback: Optional[str] = Field(
        description="any feedback, warnings or things to take into consideration for executing the plan"
    )
