from pydantic import BaseModel, Field


class ActingOutput(BaseModel):
    current_status: str = Field(
        description="Evaluation on the current status of the task description. Either 'far from completion', 'close to completion' or 'completed'"
    )
    context: str = Field(
        description="Description on the current status of the task, which will be usfeul for a planner to identify the next steps to take"
    )
    result: str = Field(
        description="Answer or result to the main task (not the current step) based on the information gathered from all the previous steps. It is not an evaluation, is the content of the answer (e.g a research report)."
    )
