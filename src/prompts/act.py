ACT_ACTION_PROMPT = """You are tasked with determining the current status of the main task after reviewing its recent progress and outcomes.

The success of the execution of the current step was evaluated by an expert, and was set as the following boolean: {success}.

This evaluator left some comments for taking into account:
```
{comments}
```

And some suggestions:
```
{suggestions}
```

Based on the current context outlined below:
"{context}"

Considering the current result of the main task:
"{result}"

And the result of the current step (not the tasl):
"{step_result}"

Your goal is to provide:
- **An evaluation of the current status of the task**: Is the task description ("{task_description}") far from completion, close to completion, or fully completed?
- **A concise description of the current status**: This should help the next phase (planning) determine the appropriate actions to take.
- **An updated global answer**: This would be tha answer to the main task with the steps taken until now. For example, for a research, it would be the complete content of the research (title, sections, conclusions, etc.). It's different from the evaluation status.

Follow these instructions:
- Be clear and direct, focusing on the immediate task status and its implications.
- MAKE SURE YOU ARE EVALUATING THE TASK COMPLETION, NOT THE STEP. Think, is the current result of the main task answering the request of the task description?
- Do not be over demanding when evaluating the status. Check within the next steps, some would be useful, but if none is needed mark it as complete.

PLEASE, express your response as a JSON object. Not providing more information than requested, just provide the following JSON.
{format_instructions}
"""
