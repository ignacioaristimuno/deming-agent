PLAN_ACTION_PROMPT = """You excel at planning the steps required for an LLM to be able to solve the main task mentioned before.
Your task is to propose a series of simple steps that will break down the complexity of the main task, in order for a later process to use these steps as input.

Based on the current context outlined below:
"{context}"

Develop a detailed action plan that includes:
- Clear objectives
- Specific steps to achieve these objectives
- Anticipated outcomes

Avoid repeating steps that were already being made. Here's a list of the steps that were previously taken:
```
{previous_steps}
```

Follow these instructions:
- Be concise
- Avoid adding validation or evaluation steps. That should happen in the Check phase of a Deming Cycle (step).
- Avoid unnecessary steps, if just one step could be enough (and its not too complex) propose just one step.
- Remember this is LLM-based. No images, videos or audios should be included.
- DO NOT REPEAT STEPS ALREADY MADE.

Ensure that your plan addresses any challenges noted in the feedback and stays relevant to the current context.
Also, make sure that the proposed steps are achievable by an LLM, and are not far fetched.

**Good Planning Example 1** (dont copy the output format, its just a reference):
```
Steps needed for performing the task "Do a research report of Vision Transformers":
1. Propose titles for sections within the report and include information of DOs and DONT's for writing that section (but do not write the sections).
2. Iterate over each section, writing one section at a time (each section must be a separate step in the flow). You may web search for each section as needed.
4. After all the sections are completed, create a single, unified report containing all the subsections. Include a catchy title, a TL;DR and a conclusion or key findinds.
```

**Good Planning Example 2** (dont copy the output format, its just a reference):
```
Steps needed for performing the task "Is the current weather common in Montevideo?":
1. Perform web search to extract the current weather in Montevideo. Sintetize the information.
2. Perform web search to extract what is the weather like in Montevideo arount the current date (this year and previous years). Sintetize the findings.
3. Make a comparison between the current weather and the common weather providing a response.
```

**Bad Planning Example 2** (dont copy the output format, its just a reference of what NOT to do):
```
Steps needed for performing the task "Summary of trends in AI Agents":
1. Write a summary of trends in AI agents (without breaking down into smaller peaces and not using web search)
2. Evaluate the summary.
```

PLEASE, express your response as a JSON object. Not providing more information than requested, just provide the following JSON.
{format_instructions}
"""
