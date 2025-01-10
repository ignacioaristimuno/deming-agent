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


def extract_json(content: str) -> str:
    """
    Extract JSON content from a given string.

    Args:
        content (str): The input string

    Returns:
        str: The JSON content extracted from the string
    """

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
    """
    Call a model with a given prompt and input variables.

    Args:
        state (State): The current state of the agent
        config (RunnableConfig): The configuration for the agent
        custom_prompt (str): The custom prompt to use for the model
        action (DemingAction): The current action of the agent
        allow_tools (bool, optional): If True, allow the model to use tools. Defaults to False.
        input_variables (dict, optional): The input variables to use for the model. Defaults to None.

    Returns:
        AIMessage: The response from the model
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
    """
    Plan the next steps required to solve the main task.

    This function is responsible for setting up the task description and generating
    a plan using the provided state and configuration. It constructs a planning prompt,
    calls a model to generate the plan, and updates the state with the next steps and
    any relevant messages.

    Args:
        state (State): The current state of the agent, containing task context and history.
        config (RunnableConfig): The configuration settings for the agent's execution.

    Returns:
        None: The function updates the state with the planned next steps and does not return a value.
    """

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
    """
    Execute the next step in the plan.

    This function is responsible for setting up the next step and generating
    a prompt for the model to execute the step. It constructs an execution prompt,
    calls a model to execute the step, and updates the state with the step's results
    and any relevant messages.

    Args:
        state (State): The current state of the agent, containing task context and history.
        config (RunnableConfig): The configuration settings for the agent's execution.

    Returns:
        None: The function updates the state with the results of the executed step and does not return a value.
    """

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
    """
    Evaluate the results of the current step and generate feedback.

    This function is responsible for setting up the evaluation prompt,
    calling a model to generate the evaluation, and updating the state
    with the evaluation and any relevant messages.

    Args:
        state (State): The current state of the agent, containing task context and history.
        config (RunnableConfig): The configuration settings for the agent's execution.

    Returns:
        None: The function updates the state with the evaluation and does not return a value.
    """

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
    """
    Determine the current status of the main task.

    This function evaluates the current status of the main task by reviewing
    the recent progress and outcomes. It constructs an action prompt, calls
    a model to generate the action response, and updates the state with the
    evaluation of the task's completion status and any relevant messages.

    Args:
        state (State): The current state of the agent, containing task context and history.
        config (RunnableConfig): The configuration settings for the agent's execution.

    Returns:
        dict: A dictionary containing the evaluation of the current status, context,
              results, and messages from the action response.
    """

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
    """
    Generate the final answer for the task in Markdown format.

    This function constructs a final answer prompt using the task description
    and the current results, then calls a model to generate the final answer.
    The generated answer is returned as a formatted string.

    Args:
        state (State): The current state of the agent, containing task context and relevant results.
        config (RunnableConfig): The configuration settings for the agent's execution.

    Returns:
        dict: A dictionary containing the final answer in Markdown format.
    """

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
    """
    Determine whether to proceed with acting or redoing the current step.

    If the step was successful or the maximum number of retries has been exceeded, proceed to the act phase.
    Otherwise, redo the current step.
    """

    if state.success or state.n_retries > MAX_N_RETRIES:
        return "act"
    else:
        return "do"


def route_after_act_phase(
    state: State,
) -> Literal["final_answer_generation", "clean_vars"]:
    """
    Determine the next step in the workflow based on the current status of the task.

    If the task is completed, proceed to the final answer generation phase.
    Otherwise, proceed to the clean variables phase to clean up variables used during the current step.
    """

    if state.current_status == "completed":
        return "final_answer_generation"
    else:
        return "clean_vars"


def route_tools_usage(
    state: State,
) -> Literal["check", "tools"]:
    """
    Route the workflow to the check or tools phase based on the existence of tool calls in the last message.

    If the last message contains tool calls, the workflow proceeds to the tools phase to execute the requested actions.
    Otherwise, it proceeds to the check phase to evaluate the results of the current step.

    Args:
        state (State): The current state of the agent.

    Returns:
        Literal["check", "tools"]: The next phase in the workflow.
    """

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


def clean_step_vars(state: State) -> None:
    """
    Reset step-specific variables to their default values.

    This function resets the variables that are specific to the current step,
    such as the step results, obstacles, number of retries, success status, and
    feedback. This is done to prepare for the next step in the workflow.

    Args:
        state (State): The current state of the agent.

    Returns:
        dict: A dictionary with the default values for the step-specific variables.
    """

    return {
        "step_results": None,
        "step_obstacles": None,
        "n_retries": 0,
        "success": False,
        "feedback": None,
        "step_search_triggered": False,
    }
