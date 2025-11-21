"""
Azure Functions entry point for Wallet Service
Wraps the FastAPI application using ASGI
"""

import azure.functions as func
from main import app as fastapi_app

# Create Azure Functions app
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Wrap FastAPI app as ASGI
@app.function_name(name="WalletServiceFunction")
@app.route(route="{*route}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function that proxies all HTTP requests to FastAPI app
    """
    return await func.AsgiMiddleware(fastapi_app).handle_async(req)
