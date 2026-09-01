from app.agents.email_agent import agent

result = agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": """
            Analyze this email:
            
            Subject: Production Server Down
            
            
            Body: The production server is currently unavailable.
            Customers cannot access the application. Please investigate.\
            immediately and inform the technical team.
            """
        }
    ]
})

print(result)