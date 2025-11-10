from strands import Agent, tool

CLAIM_DETECTION_ASSISTANT_SYSTEM_PROMPT = """
You are an assistant specialized in identifying erroneous or misleading claims in text.

Instructions:
- Break down the input text into separate statements.
- For each statement, determine if it contains misinformation, disinformation, or is otherwise clearly false or misleading.
- Fact-check statements using general knowledge and logical reasoning. Look for fabrication, manipulation, or critical omissions.

Output:
- Return a numbered list of all statements you identify as erroneous, incorrect, or misleading.
- Each listed item should be the erroneous claim as a direct quotation.
- If there are no erroneous statements, return 'No erroneous claims found.'
- Do not return any explanations, extra text, or formatting.

Example 1
Input:
Climate change is a hoax invented by scientists. The Great Wall of China is visible from space.

Output:
1. "Climate change is a hoax invented by scientists."
2. "The Great Wall of China is visible from space."

Example 2
Input:
The Pacific Ocean is the largest ocean on Earth. Drinking bleach can cure illnesses.

Output:
1. "Drinking bleach can cure illnesses."

Example 3
Input:

Output:
No erroneous claims found.
"""


@tool
def claim_detection_assistant(query: str) -> str:
    """
    Analyze free text, segment it into statements, and flag each for erroneous claim.

    Args:
        query: Free-form text containing one or more statements

    Returns:
        The potentially erroneous claims.
    """
    formatted_query = f"Please identify erroneous or misleading claims with supporting evidence and context: {query}"

    try:
        research_agent = Agent(
            model="anthropic.claude-3-5-haiku-20241022-v1:0",
            system_prompt=CLAIM_DETECTION_ASSISTANT_SYSTEM_PROMPT,
        )

        agent_response = research_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response

        return "I apologize, but I couldn't identify any erroneous claims. Please check if your query is clearly stated or try rephrasing it."
    except Exception as e:
        # Return specific error message for math processing
        return f"Error identifying erroneous claims: {str(e)}"
