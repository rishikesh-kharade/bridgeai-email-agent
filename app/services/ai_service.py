import os
from dotenv import load_dotenv
from google import genai

from app.schemas.ai_analysis import AIAnalysis
load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def analyze_email(subject: str, body: str) -> AIAnalysis:
    prompt = f"""
    You are BridgeAI's Email Analysis Agent.

    Analyze the following business email.

    Determine:
    - A concise 2-3 sentence summary
    - The appropriate category
    - Priority: Critical, High, Medium, or Low
    - Sentiment: Positive, Neutral, or Negative
    - Whether action is required
    - Whether the email requires attention
    - Specific action items if action is required

    category: AICategory
    
    Determine the most appropriate category based on the email content.
    The category is not restricted to a predefined list.
    Create a meaningful category that accurately represents the email.

    Priority and sentiment must be determined independently.

    Do not perform any actions.
    Do not modify any database.
    Only analyze the email and return the requested structured result.

    Subject:
    {subject}

    Body:
    {body}
    """

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": AIAnalysis,
        },
    )

    return AIAnalysis.model_validate_json(response.text)  