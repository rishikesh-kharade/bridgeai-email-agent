from app.services.ai_service import analyze_email

subject = "Production Server Down"

body = """
Our production server is down and customers cannot access the application.
Please investigate immediately and notify the technical team.
"""

result = analyze_email(subject, body)

print(result)
print(result.model_dump())