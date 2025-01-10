CHECK_ACTION_PROMPT = """You are excellent at reviewing and assessing the outcomes of tasks to ensure their accuracy and completeness.
Your task is to **evaluate the results** of the following completed step: "{current_step}".

The current results of the step are the following (if existent):
```
{step_results}
```

The current global results are the following (if existent):
```
{results}
```

Where some obstacles while executing this step where identified (if any):
```
{obstacles}
```

Based on the current context outlined below:
"{context}"

Considering the feedback from previous actions:
"{previous_feedback}"

To complete this task:
- **Review the results of the step** and check if the objectives were fully met.
- **Identify any discrepancies** or gaps in the execution.
- **Determine if any further adjustments** are necessary or if the results can proceed to the next phase.
- **Provide clear feedback** on the success or issues found during the review.

Ensure that:
- The evaluation is thorough, focusing on the alignment of the result with the task's objectives.
- Any missing or incorrect information is noted.
- A concise summary of findings and suggestions for improvement (if needed) are provided.

PLEASE, express your response as a JSON object. Not providing more information than requested, just provide the following JSON.
{format_instructions}
"""
