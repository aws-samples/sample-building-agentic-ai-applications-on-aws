# Agentic AI workshop

## Fact Check Assistant

## Overview

In this workshop you will learn how to build an Agentic AI powered fact-checking assistant. You will begin with a simple use case and then gradually add complexity using multi-agent collaboration systems. You will also learn about different frameworks and libraries that can be used to build intelligent fact-checking agents. Specifically at the end of the workshop you will learn how to:

1. Build a multi-agent fact-checking system using [Strands Agents](https://strandsagents.com/latest/)
2. Create specialized agents for mathematical verification, claim identification, and evidence-based fact-checking
3. Integrate MCP (Model Context Protocol) servers for real-time web search capabilities using DuckDuckGo
4. Build a supervisor agent that orchestrates multiple specialized sub-agents for comprehensive content analysis
5. Implement systematic misinformation detection workflows with evidence-based assessments

### Environment Variables

Create a `.env` file in the `src/frontend` directory with the following variables:

```

LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com

```

> Note: Langfuse is used for observability. You can sign up for a free account at [langfuse.com](https://langfuse.com).

### Install Dependencies

Run the following command to install the required dependencies:

```bash
pip install -r src/frontend/requirements.txt
```

### Directory Structure

- `/Fact_Check_Assistant/` - Contains all workshop materials

  - `/1_strands-agents-multi-agent/` - Notebooks to build and deploy agent
  - `/src/` - Source code for the fact-check assistant application
    - `frontend` - Streamlit app running fact-check assistant application
    - `infra` - CDK infrastructure for the fact-check assistant application

## Sample prompts:

At the end of the workshop, the fact-checking assistant will be able to handle multiple types of verification queries, including:

- "The Great Wall of China is visible from the Moon with the naked eye."
- "The average mortgage interest rate in Australia is 1.5%, which means on a $500,000 loan over 30 years, you'll pay just $250,000 in total interest."
- "Drinking lemon water every morning can cure diabetes by neutralizing blood sugar levels."
- "If you invest $10,000 at a 7% annual return compounded monthly, you'll have approximately $20,000 after 10 years."

For an overview of the various labs go the overview page [here](./../README.md). To get started with the first lab, go [here](./1_strands-agents-multi-agent)
