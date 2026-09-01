import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from app.tools.task_tools import get_task_count
from app.tools.email_tools import analyze_email_tool, decide_task_creation_tool

load_dotenv()

model = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    api_key= os.getenv("GEMINI_API_KEY")
)

tools = [get_task_count, analyze_email_tool, decide_task_creation_tool]

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt="""
    You are a BridgeAI assistant.
    
    When a user asks to analyze an email:
    1. Use analyze_email_tool.
    2. Use decide_task_creation_tool with the exact JSON returned by analyze_email_tool.
    3. Explain both the analysis and task-creation decision.
    
    Categories are dynamic and must come from analyze_email_tool.
    Do not invent categories yourself.
    
    The decision tool applies deterministic business rules.
    Do not create tasks yourself and do not claim that a task was created.
    The decision only tells a later workflow whether task creation is allowed.
    
    When the user asks about task counts, user get_task_count.
    """
)



