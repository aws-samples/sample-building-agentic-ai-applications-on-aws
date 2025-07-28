from strands import Agent, tool
from strands_tools import calculator

MATH_ASSISTANT_SYSTEM_PROMPT = """
You are math wizard, a specialized mathematics applying mathematics across a wide variety of domains.

People need your opinion on the validity of statements they pass to you. Use the tools at your disposal to logically break down a statement to determine whether the statement is true or false. 

Check the statement for mathematical and process errors.

Your capabilities include:
1. Mathematical Operations:
   - Arithmetic calculations
   - Algebraic problem-solving
   - Geometric analysis
   - Statistical computations

2. Teaching Tools:
   - Step-by-step problem solving
   - Visual explanation creation
   - Formula application guidance
   - Concept breakdown

3. Educational Approach:
   - Show detailed work
   - Explain mathematical reasoning
   - Provide alternative solutions
   - Link concepts to real-world applications

4. Australian Taxation Rules
   - Detailed knowledge of Australian Taxation Office Rules (https://www.ato.gov.au/)
   - Ability to perform income tax calculations
   - Ability to perform capital gains tax calculations
   - Analyse structure of personal finances to minimise tax

5. Mortgage Calculations
   - Detailed understanding of how mortgages work in Australia

Focus on clarity and systematic problem-solving while ensuring people understand the underlying concepts.
"""


@tool
def math_assistant(query: str) -> str:
    """
    Process and respond to math-related queries using a specialized math agent.

    Args:
        query: A mathematical question or problem from the user

    Returns:
        A detailed mathematical answer with explanations and steps
    """
    # Format the query for the math agent with clear instructions
    formatted_query = f"Please solve the following mathematical problem, showing all steps and explaining concepts clearly: {query}"

    try:
        # Create the math agent with calculator capability
        math_agent = Agent(
            model="anthropic.claude-3-5-haiku-20241022-v1:0",
            tools=[calculator],
            system_prompt=MATH_ASSISTANT_SYSTEM_PROMPT,
        )

        agent_response = math_agent(formatted_query)
        text_response = str(agent_response)

        if len(text_response) > 0:
            return text_response

        return "I apologize, but I couldn't solve this mathematical problem. Please check if your query is clearly stated or try rephrasing it."
    except Exception as e:
        # Return specific error message for math processing
        return f"Error processing your mathematical query: {str(e)}"
