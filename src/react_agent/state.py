"""Define the state structures for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep
from typing_extensions import Annotated

from src.structs import (
    DemingAction,
    PlanningStep,
    CheckingOutput,
)


@dataclass
class InputState:
    """Defines the input state for the agent, representing a narrower interface to the outside world.

    This class is used to define the initial state and structure of incoming data.
    """

    messages: Annotated[Sequence[AnyMessage], add_messages] = field(
        default_factory=list
    )


@dataclass
class State(InputState):
    """Represents the complete state of the agent, extending InputState with additional attributes.

    This class can be used to store any information needed throughout the agent's lifecycle.
    """

    # Steps
    is_last_step: IsLastStep = field(default=False)
    current_action: DemingAction = field(default=None)
    steps_taken: List[PlanningStep] = field(default=list)

    # Input
    task_description: str = field(default=None)

    # Output
    final_answer: str = field(default=None)

    # Plan
    next_steps: List[PlanningStep] = field(default=list)
    already_processed_steps: List[PlanningStep] = field(default=list)

    # Do
    step_results: str = field(default=None)
    step_obstacles: str = field(default=None)
    step_search_triggered: bool = field(default=False)
    n_retries: int = 0

    # Check
    success: bool = field(default=False)
    feedback: CheckingOutput = field(default=None)

    # Act
    current_status: str = field(default=None)
    context: str = field(default=None)
    results: str = field(default=None)
