from ast import literal_eval
from datetime import datetime, timezone
import json
from typing import List, Literal, cast

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableConfig

from react_agent.configuration import Configuration
from react_agent.state import State
from react_agent.tools import TOOLS
from react_agent.utils import load_chat_model
from src.prompts import (
    PLAN_ACTION_PROMPT,
    DO_ACTION_PROMPT,
    CHECK_ACTION_PROMPT,
    ACT_ACTION_PROMPT,
    FINAL_ANSWER_PROMPT,
)
from src.settings import custom_logger
from src.structs import (
    PlanningOutput,
    DoingOutput,
    CheckingOutput,
    ActingOutput,
    DemingAction,
)


logger = custom_logger("Actions")

MAX_N_RETRIES = 3


# Pydantic Output Parsers
planning_parser = PydanticOutputParser(pydantic_object=PlanningOutput)
doing_parser = PydanticOutputParser(pydantic_object=DoingOutput)
checking_parser = PydanticOutputParser(pydantic_object=CheckingOutput)
acting_parser = PydanticOutputParser(pydantic_object=ActingOutput)


def extract_json(content):
    """Function to extract the JSON content from responses."""

    try:
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.replace("\n", "")
        content = content.strip()
        content = json.loads(content)
        return content
    except ValueError as e:
        raise ValueError("JSON could not be extracted")


async def call_model(
    state: State,
    config: RunnableConfig,
    custom_prompt: str,
    action: DemingAction,
    allow_tools: bool = False,
    input_variables: dict = None,
) -> AIMessage:
    """Call the LLM powering our "agent".

    This function prepares the prompt, initializes the model, and processes the response.

    Args:
        state (State): The current state of the conversation.
        config (RunnableConfig): Configuration for the model run.

    Returns:
        dict: A dictionary containing the model's response message.
    """
    configuration = Configuration.from_runnable_config(config)

    # Create a prompt template. Customize this to change the agent's behavior.
    system_prompt = configuration.system_prompt.format(
        task_description=state.task_description,
        phase=state.current_action,
        context=state.context,
        system_time=datetime.now(tz=timezone.utc).isoformat(),
        previous_feedback=None if state.feedback is None else state.feedback.comments,
        available_tools="web search",
        current_action=action,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", custom_prompt.template),
        ]
    )

    # Initialize the model with tool binding. Change the model or add more tools here.
    if allow_tools:
        model = load_chat_model(configuration.model).bind_tools(TOOLS)
    else:
        model = load_chat_model(configuration.model)

    # Prepare the input for the model, including the current system time
    message_value = await prompt.ainvoke(
        input_variables,
        config,
    )
    print(f"Message value (LLM call): {message_value}")

    # Get the model's response
    response = cast(AIMessage, await model.ainvoke(message_value, config))
    print(f"Model call response (type: {type(response)}): {response}")

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        return AIMessage(
            id=response.id,
            content="Sorry, I could not find an answer to your question in the specified number of steps.",
        )
    return response


async def plan_action(state: State, config: RunnableConfig) -> None:
    """Plan the next action based on the current context."""

    # Set task description if not set
    if state.task_description is None:
        state.task_description = state.messages[0].content

    prompt = PromptTemplate(
        template=PLAN_ACTION_PROMPT,
        input_variables=["context", "previous_steps", "format_instructions"],
    )
    print(f"Planning prompt: {prompt}")

    action_response = await call_model(
        state,
        config=config,
        custom_prompt=prompt,
        input_variables={
            "context": state.context,
            "previous_steps": (
                ", ".join(
                    [plan_step.step for plan_step in state.already_processed_steps]
                )
                if isinstance(state.already_processed_steps, list)
                else None
            ),
            "format_instructions": planning_parser.get_format_instructions(),
        },
        allow_tools=False,
        action=DemingAction.PLAN,
    )
    print(f"Planning phase: {action_response}")
    action_content = extract_json(action_response.content)
    action_content = PlanningOutput(**action_content)
    return {
        "next_steps": action_content.next_steps,
        "messages": [action_response],
        "task_description": state.task_description,
    }


async def do_action(
    state: State,
    config: RunnableConfig,
) -> None:
    """Execute a specific task."""

    prompt = PromptTemplate(
        template=DO_ACTION_PROMPT,
        input_variables=[
            "current_step",
            "current_step",
            "step_expected_outcome",
            "context",
            "previous_feedback",
            "format_instructions",
        ],
    )
    print(f"Step search triggered: {state.step_search_triggered}")

    action_response = await call_model(
        state,
        config=config,
        custom_prompt=prompt,
        input_variables={
            "current_step": state.next_steps[0].step,
            "step_details": state.next_steps[0].details,
            "step_expected_outcome": state.next_steps[0].expected_outcome,
            "context": state.context,
            "previous_feedback": state.feedback,
            "format_instructions": doing_parser.get_format_instructions(),
        },
        allow_tools=True if state.step_search_triggered == False else False,
        action=DemingAction.DO,
    )
    print(f"Execution phase: {action_response}")

    # Check if tool calling was triggered
    if action_response.response_metadata["finish_reason"] == "tool_calls":
        return {"messages": [action_response], "step_search_triggered": True}

    action_content = extract_json(action_response.content)
    action_content = DoingOutput(**action_content)
    return {
        "step_results": action_content.result,
        "step_obstacles": action_content.obstacles,
        "n_retries": state.n_retries + 1,
        "messages": [action_response],
    }


async def check_action(state: State, config: RunnableConfig) -> None:
    """Integrate feedback from previous tasks into the agent's strategy."""

    prompt = PromptTemplate(
        template=CHECK_ACTION_PROMPT,
        input_variables=[
            "current_step",
            "step_results",
            "results",
            "obstacles",
            "context",
            "previous_feedback",
            "format_instructions",
        ],
    )

    action_response = await call_model(
        state,
        config=config,
        custom_prompt=prompt,
        input_variables={
            "current_step": state.next_steps[0].step,
            "step_results": state.step_results,
            "results": state.results,
            "obstacles": state.step_obstacles,
            "context": state.context,
            "previous_feedback": state.feedback,
            "format_instructions": checking_parser.get_format_instructions(),
        },
        allow_tools=False,
        action=DemingAction.CHECK,
    )
    print(f"Evaluation phase: {action_response}")
    action_content = extract_json(action_response.content)
    action_content = CheckingOutput(**action_content)

    already_processed_steps = (
        state.already_processed_steps + [state.next_steps[0]]
        if isinstance(state.already_processed_steps, list)
        else [state.next_steps[0]]
    )
    return {
        "success": action_content.success,
        "feedback": action_content,
        "messages": [action_response],
        "already_processed_steps": already_processed_steps + [state.next_steps[0]],
    }


async def act_action(state: State, config: RunnableConfig) -> None:
    """Make a decision based on the current circumstances."""

    prompt = PromptTemplate(
        template=ACT_ACTION_PROMPT,
        input_variables=[
            "success" "comments",
            "suggestions",
            "context",
            "result",
            "step_result",
            "format_instructions",
        ],
    )

    action_response = await call_model(
        state,
        config=config,
        custom_prompt=prompt,
        input_variables={
            "task_description": state.task_description,
            "success": state.success,
            "comments": state.feedback.comments,
            "suggestions": state.feedback.suggestions,
            "context": state.context,
            "result": state.results,
            "step_result": state.step_results,
            "format_instructions": acting_parser.get_format_instructions(),
        },
        allow_tools=False,
        action=DemingAction.ACT,
    )
    print(f"Act phase: {action_response.content}")
    action_content = extract_json(action_response.content)
    action_content = ActingOutput(**action_content)
    return {
        "current_status": action_content.current_status,
        "context": action_content.context,
        "results": action_content.result,
        "messages": [action_response],
    }


async def generate_final_answer(
    state: State,
    config: RunnableConfig,
) -> None:
    """Generate the final answer based on the content provided."""

    prompt = PromptTemplate(
        template=FINAL_ANSWER_PROMPT,
        input_variables=[
            "task_description",
            "current_result",
        ],
    )
    print(f"Step search triggered: {state.step_search_triggered}")

    action_response = await call_model(
        state,
        config=config,
        custom_prompt=prompt,
        input_variables={
            "task_description": state.task_description,
            "current_result": state.results,
        },
        allow_tools=False,
        action=None,
    )
    print(f"Final answer generation phase: {action_response}")
    action_content = action_response.content
    return {"final_answer": action_content}


def route_after_check_phase(state: State) -> Literal["act", "do"]:
    """Determine whether to continue to the Act phase or retry the Do phase if the evaluation was not successful"""

    if state.success or state.n_retries > MAX_N_RETRIES:
        return "act"
    else:
        return "do"


def route_after_act_phase(
    state: State,
) -> Literal["final_answer_generation", "clean_vars"]:
    """Determine whether to continue with a next iteration or the task is completed"""

    if state.current_status == "completed":
        return "final_answer_generation"
    else:
        return "clean_vars"


def route_tools_usage(
    state: State,
) -> Literal["check", "tools"]:
    """Identify whether to use tools for the do phase or not"""

    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    # If there is no tool call, then we continue to the check phase
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return "check"

    # Otherwise we execute the requested actions
    return "tools"


def clean_step_vars(
    state: State,
) -> None:
    """Step for cleaning the variables using during the current step for performing the next step"""

    return {
        "step_results": None,
        "step_obstacles": None,
        "n_retries": 0,
        "success": False,
        "feedback": None,
        "step_search_triggered": False,
    }
