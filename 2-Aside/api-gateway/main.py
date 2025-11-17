"""
API Gateway for 2-Aside Platform
Routes requests to appropriate microservices
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="2-Aside API Gateway",
    description="Central API Gateway for 2-Aside Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "2-Aside API Gateway",
        "services": {
            "auth": "http://localhost:8001",
            "wallet": "http://localhost:8002",
            "user": "http://localhost:8003",
            "funding": "http://localhost:8004"
        }
    }
