import base64
import logging
import os
import sys

from dotenv import load_dotenv

# Import assistant modules from the same directory
from mcp import StdioServerParameters, stdio_client
from strands import Agent, tool
from strands.tools.mcp import MCPClient

# Get the absolute path to the backend directory (where this script is located)
backend_dir = os.path.dirname(os.path.abspath(__file__))

# Add the backend directory to the Python path
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from claim_detection_assistant import claim_detection_assistant
from math_assistant import math_assistant
from research_assistant import research_assistant

SUPERVISOR_SYSTEM_PROMPT = """
You are a sophisticated misinformation detection orchestrator that coordinates specialized agents for comprehensive content analysis and fact-checking. Your primary mission is to detect, analyze, and verify information for potential misinformation.

## Available Specialized Agents

You have access to these specialized agents:

1. **claim_detection_assistant** - Claim Detection Assistant
   - Breaks down input text into separate statements
   - Identifies potentially false or misleading claims
   - Returns a numbered list of erroneous claims as direct quotations
   - Use for: Initial content analysis, statement extraction, identifying suspicious claims

2. **research_assistant** - External Fact Checker Assistant
   - Performs deep fact-checking with evidence using DuckDuckGo search
   - Searches reliable sources and cross-references information
   - Provides TRUE/FALSE/PARTIALLY TRUE verdicts with supporting evidence
   - Use for: Verifying specific claims, finding authoritative sources, detailed fact-checking

3. **math_assistant** - Math Wizard
   - Validates mathematical claims and calculations
   - Checks numerical accuracy and statistical validity
   - Analyzes quantitative statements for errors
   - Use for: Mathematical fact-checking, statistical claims, numerical verification

## Orchestration Strategy

For comprehensive misinformation detection, follow this multi-step approach:

### Step 1: Initial Analysis
- Use **claim_detection_assistant** to segment content and identify potentially problematic statements
- This provides a structured list of all claims that need verification

### Step 2: Specialized Verification
- For mathematical/statistical claims → Use **math_assistant**
- For factual claims requiring evidence → Use **research_assistant**
- For complex claims → Coordinate multiple agents as needed

### Step 3: Synthesis
- Combine results from all agents
- Provide concise assessment with evidence
- Highlight the most concerning misinformation risks

## Trigger Keywords for Misinformation Analysis

Always initiate the multi-agent workflow when you detect:
- "fact-check", "verify claims", "check if true"
- "misinformation", "disinformation", "fake news", "suspicious content"
- Any request to evaluate content truthfulness

## Best Practices

1. **Always start with claim_detection_assistant** for content segmentation
2. **Use research_assistant** for claims requiring external verification
3. **Use math_assistant** for any numerical or statistical claims
4. **Coordinate multiple agents** for comprehensive analysis
5. **Provide clear, evidence-based conclusions**

Your goal is to provide concise, accurate misinformation detection by leveraging the specialized capabilities of each agent in a coordinated manner.
"""

# --- Langfuse & OTEL Observability Setup ---

# Specify the path to your .env file (in the same directory as this script)
env_path = os.path.join(backend_dir, ".env")

# Load the environment variables from the specified file
load_dotenv(dotenv_path=env_path)

# Configure langfuse for observability
LANGFUSE_AUTH = base64.b64encode(
    f"{os.environ.get('LANGFUSE_PUBLIC_KEY')}:{os.environ.get('LANGFUSE_SECRET_KEY')}".encode()
).decode()

# Handle case where LANGFUSE_HOST might be None
langfuse_host = os.environ.get("LANGFUSE_HOST")
if langfuse_host:
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = (
        langfuse_host + "/api/public/otel/v1/traces"
    )
else:
    logging.warning(
        "LANGFUSE_HOST environment variable not set, skipping OTEL configuration"
    )

os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"


# Start MCP client with error handling
def create_mcp_client():
    """Create MCP client with fallback handling"""
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
        logging.warning(f"Failed to create MCP client: {e}")
        return None


stdio_mcp_client = create_mcp_client()


## Create Supervisor Agent for Fact Checking
@tool
def fact_check_supervisor(query: str) -> str:
    """
    Process queries through the multi-agent fact-checking system.

    Args:
        query: The text to analyze for factual accuracy

    Returns:
        str: A comprehensive fact-check assessment
    """
    # Check if MCP client is available
    if stdio_mcp_client is not None:
        try:
            # Use MCP client context manager to ensure session is active
            with stdio_mcp_client:
                # Combine custom tools with MCP tools
                all_tools = [
                    math_assistant,
                    claim_detection_assistant,
                    research_assistant,
                ]

                # Create the supervisor agent within MCP context
                supervisor = Agent(
                    model="anthropic.claude-3-5-haiku-20241022-v1:0",
                    system_prompt=SUPERVISOR_SYSTEM_PROMPT,
                    tools=all_tools,
                )

                # Process the query within the same MCP context
                return supervisor(
                    f"Provide a comprehensive fact-check assessment for this text: {query}"
                )

        except Exception as e:
            logging.error(f"Error processing query with MCP tools: {str(e)}")

    # Fallback to supervisor without MCP tools
    logging.info("Using fallback mode without MCP tools")
    supervisor = Agent(
        model="anthropic.claude-3-5-haiku-20241022-v1:0",
        system_prompt=SUPERVISOR_SYSTEM_PROMPT,
        tools=[
            math_assistant,
            claim_detection_assistant,
        ],
    )

    return supervisor(
        f"Provide a comprehensive fact-check assessment for this text: {query}"
    )
