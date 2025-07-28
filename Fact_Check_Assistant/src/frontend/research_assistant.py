from mcp import StdioServerParameters, stdio_client
from strands import Agent, tool
from strands.tools.mcp import MCPClient

RESEARCH_ASSISTANT_SYSTEM_PROMPT = """
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

def create_research_mcp_client():
    """Create MCP client for research with error handling"""
    try:
        return MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="uvx",
                    args=["duckduckgo-mcp-server"],
                )
            )
        )
    except Exception as e:
        print(f"Failed to create research MCP client: {e}")
        return None

stdio_mcp_client = create_research_mcp_client()


@tool
def research_assistant(query: str) -> str:
    """
    Fact-check a statement and return whether it's true or false with supporting context.

    Args:
        statement: The statement or claim to fact-check

    Returns:
        A fact-check assessment with verdict (TRUE/FALSE/PARTIALLY TRUE) and supporting evidence
    """
    formatted_query = f"Please fact-check this statement and provide a clear verdict (TRUE/FALSE/PARTIALLY TRUE) with supporting evidence and context: {query}"

    # Check if MCP client is available
    if stdio_mcp_client is not None:
        try:
            print("Routed to Fact Checker with MCP")
            with stdio_mcp_client:
                # Get the tools from the MCP server
                tools = stdio_mcp_client.list_tools_sync()

                # Create an agent with MCP tools and fact-checking prompt
                fact_checker_agent = Agent(
                    model="anthropic.claude-3-5-haiku-20241022-v1:0",
                    tools=tools,
                    system_prompt=RESEARCH_ASSISTANT_SYSTEM_PROMPT,
                )
                agent_response = fact_checker_agent(formatted_query)
                text_response = str(agent_response)

                if len(text_response) > 0:
                    return text_response

                return "I apologize, but I couldn't fact-check this statement. Please provide a clear, specific claim to verify."
        except Exception as e:
            print(f"MCP fact-checking failed, using fallback: {e}")

    # Fallback without MCP tools
    print("Using fallback fact-checking without external search")
    fallback_agent = Agent(
        model="anthropic.claude-3-5-haiku-20241022-v1:0",
        system_prompt=RESEARCH_ASSISTANT_SYSTEM_PROMPT,
    )
    
    try:
        agent_response = fallback_agent(formatted_query)
        text_response = str(agent_response)
        
        if len(text_response) > 0:
            return f"[Note: Limited fact-checking without external search] {text_response}"
        
        return "I apologize, but I couldn't fact-check this statement without external search capabilities."
    except Exception as e:
        return f"Error during fallback fact-checking: {str(e)}"
