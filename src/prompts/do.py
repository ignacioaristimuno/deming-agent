DO_ACTION_PROMPT = """You excel at executing individual steps that contribute to solving a larger task.
Your task is to perform the following step from the plan: "{current_step}".

Details on the step to take: "{step_details}".

Expected outcome of the step: "{step_expected_outcome}".

Based on the current context outlined below:
"{context}"

Considering the feedback from previous actions:
"{previous_feedback}"

To complete this task:
- **Execute the required actions** to accomplish this step.
- **Use web search and available tools** if necessary to gather information or perform the task.
- **Present concise and actionable results** based on the requirements of this step.

Ensure that:
- The step is completed effectively, focusing only on this specific task.
- Any challenges or blockers encountered are noted along with potential suggestions for overcoming them.
- The results are presented clearly and are ready for the next phase.

PLEASE, express your response as a JSON object. Not providing more information than requested, just provide the following JSON.
{format_instructions}
"""
