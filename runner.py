from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types
from tool import  gmail_unread_primary
from prompts import EMAIL_READING_PROMPT
from google.adk.models.lite_llm import LiteLlm
import os
from dotenv import load_dotenv
load_dotenv()

LITELLM_API_KEY = os.getenv("LITELLM_API_KEY")
LITELLM_API_BASE = os.getenv("LITELLM_API_BASE")

#model_1 = "google/gemini-2.5-flash-preview-09-2025"
model_1 = "openrouter/deepseek/deepseek-chat-v3-0324"
model = LiteLlm(
    model=model_1,
    api_key=LITELLM_API_KEY,
    api_base="https://openrouter.ai/api/v1",
)

app_name = "email_reading_app"
rag_agent = LlmAgent(
    model=model,
    name="email_reading_agent",
    description="An agent that reads and summarizes unread emails from a user's Gmail Primary tab.",
    instruction=EMAIL_READING_PROMPT,
    tools=[],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.15,
        max_output_tokens=10000
    ),
)

email_runner = InMemoryRunner(agent=rag_agent, app_name=app_name)

async def initialize_email_session(user_id: str):
    try:
        return await email_runner.session_service.create_session(app_name=app_name, user_id=user_id)
    except Exception as e:
        print("RAG Session init error:", e)
        return await email_runner.session_service.create_session(app_name=app_name, user_id=user_id)

async def run_email_agent_prompt(new_message: str, user_id: str):
    """
    Constructs the message, sends it to the email_runner, and returns the final text.
    Behaves exactly like your existing run_*_prompt functions (retry on session error).
    """
    session = await initialize_email_session(user_id)
    print("Email session : ", session)

    content = types.Content(role='user', parts=[types.Part.from_text(text=new_message)])

    response_text = ""

    try:
        async for event in email_runner.run_async(user_id=user_id, session_id=session.id, new_message=content):
            if event.content.parts and event.content.parts[0].text:
                response_text += event.content.parts[0].text + " "
    except Exception as e:
        print("RAG Session error, retrying:", e)
        session = await initialize_email_session(user_id)
        async for event in email_runner.run_async(user_id=user_id, session_id=session.id, new_message=content):
            if event.content.parts and event.content.parts[0].text:
                response_text += event.content.parts[0].text + " "
                
    response_text = response_text.strip()
    print(f"[RETURN] Returning {len(response_text)} chars: {response_text[:200]}...")
    return response_text if response_text else "No response from RAG agent"
