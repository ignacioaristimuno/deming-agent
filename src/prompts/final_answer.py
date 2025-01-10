FINAL_ANSWER_PROMPT = """You are tasked with creating a well-structured, concise, and clear final response in **Markdown format**. 
This response should summarize the entire process and result, ensuring it aligns with the task description.

Based on the task outlined below:
- **Task Description**: "{task_description}"

And the current gathered results:
- **Current Output to be Formatted**: "{current_result}"

Your objective is to:
1. **Present a cohesive final answer**: This should synthesize all the key information gathered during the process in a clear, well-structured manner.
2. **Ensure the answer aligns with the task description**: The response should directly address the main goal of the task.
3. **Format the output in Markdown**: Use headers, bullet points, code blocks, or other appropriate Markdown elements to make the response easy to read.

Ensure that the final answer is well-polished and clearly communicates the solution or result.

The output should align with the following structure:
- **Title**: Use `#` for creating a catchy title (or just use the task description as title)
- **TL;DR**: Provide a brief overview of the task.
- **Header**: Use `##` for section headers.
- **Conclusion**: A final summary addressing the main task, including any important conclusions.
"""
