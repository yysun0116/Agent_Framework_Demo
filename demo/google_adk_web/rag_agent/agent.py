import dotenv
dotenv.load_dotenv(override=True)

import os
from google.adk.agents import LlmAgent # for single Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters


model = LiteLlm(
    model="openai/gemma3:27b-it-qat",
    api_base=os.getenv("AGENT_BASE_URL"),
    api_key=os.getenv("AGENT_API_KEY")
)

# MCP server
rag_mcp_command = f"python3 {os.getcwd()}/../1_rag_server.py stdio"
rag_mcp_server = MCPToolset(
    connection_params = StdioServerParameters(
        command=rag_mcp_command.split(" ")[0],
        args=rag_mcp_command.split(" ")[1:],
        env={
            "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            },
    )
)

# Agent Initialization
root_agent = LlmAgent(
    model=model,
    name="seeker_agent",
    description=(
        "seeker agent that can utilize retrieval tools to help the user with their query."
    ),
    instruction=(
        "You are a helpful and intelligent assistant. The user you are helping speaks Traditional Chinese and comes from Taiwan, so in most cases, you should respond in Traditional Chinese. \n"
        "Behavior Rules: \n"
        "1. Direct Answering: If the question is clear and within your knowledge, answer directly.\n"
        "2. Retrieval-Based Answering: If the question requires specialized or external knowledge, retrieve relevant documents from the specific vector database. When retrieving from the database, the user's original intent should be preserved as much as possible, and the clarity of the question's meaning should be maintained.\n"
        "3. Clarification: If the question is vague or unclear, ask clarifying questions to understand the user’s intent before responding.\n"
    ),
    tools=[rag_mcp_server]
)