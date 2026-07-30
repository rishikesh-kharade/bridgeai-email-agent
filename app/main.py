from fastapi import FastAPI

app = FastAPI(
    title="BridgeAI Email Agent",
    description="AI-powered Email Management System",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "message": "Welcome to BridgeAI Email Agent"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
