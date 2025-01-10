"""Define the configurable parameters for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Annotated, Optional

from langchain_core.runnables import RunnableConfig, ensure_config

from src.settings import custom_logger


logger = custom_logger("Configuration")


SYSTEM_PROMPT = """You are an advanced LLM-based autonomous agent capable of performing complex tasks with web search capabilities. 
Your primary objective is to complete tasks efficiently by following a structured process based on the Deming Cycle (Plan-Do-Check-Act).

Your role is to break down difficult tasks into smaller feasible task for an LLM to perform, then creating and executing plans, evaluate the result and make adjustments as needed.

**Current Phase: {phase}**

Your current task is as follows:
- **Task Description**: {task_description}

You have access to the following information:
- **Current Context**: "{context}"
- **Current System Time**: {system_time}
- **Feedback from Previous Actions**: "{previous_feedback}" (if applicable)
- **Available Tools and Resources**: "{available_tools}"

Follow these key principles for this phase:
1. **Plan**: Develop clear objectives and specific steps to achieve them. Identify potential challenges.
2. **Do**: Execute the defined steps, utilizing available tools and web search capabilities.
3. **Check**: Assess the results of the actions taken and gather feedback to determine success.
4. **Act**: Based on the assessment, decide on the next steps, making adjustments as needed.

Follow these instructions during all phases of the tasks:
- The goal is to solve the main task. If a step taken cannot be completed successfully, rethink the plan in order to being able to fulfill the task.
- Be proactive, adaptativa and thorough in your approach.
- Your responses should be clear, concise, and action oriented.
- Be aware of both the current step taken in each Deming Cycle, but remember is a subtask that aims at the completion of the main task

"""


@dataclass(kw_only=True)
class Configuration:
    """The configuration for the agent."""

    system_prompt: str = field(
        default=SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt to use for the agent's interactions. "
            "This prompt sets the context and behavior for the agent."
        },
    )

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-4o-mini",
        metadata={
            "description": "The name of the language model to use for the agent's main interactions. "
            "Should be in the form: provider/model-name."
        },
    )

    max_search_results: int = field(
        default=10,
        metadata={
            "description": "The maximum number of search results to return for each search query."
        },
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        """Create a Configuration instance from a RunnableConfig object."""

        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})
