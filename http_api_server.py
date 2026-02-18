"""
HTTP REST API Server for MCP Tools
Exposes MCP server tools as REST endpoints for cross-application use
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from typing import List, Optional
import json
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import MCP tools
from shopify_mcp_server import create_order, get_order_status

app = FastAPI(
    title="Shopify MCP Server HTTP API",
    description="REST API wrapper for MCP server tools",
    version="1.0.0"
)

# Enable CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class LineItem(BaseModel):
    variant_id: int
    quantity: int
    title: str = "Product"
    price: float = 0.0

class CreateOrderRequest(BaseModel):
    line_items: List[LineItem]
    customer_email: str
    financial_status: str = "paid"
    test: bool = True

class GetOrderStatusRequest(BaseModel):
    order_id: int

class OrderResponse(BaseModel):
    success: bool
    data: dict
    error: Optional[str] = None

# Health check endpoint
@app.get("/")
async def root():
    return {
        "service": "Shopify MCP Server HTTP API",
        "status": "running",
        "endpoints": {
            "create_order": "/api/orders/create",
            "get_order_status": "/api/orders/status",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Create Order Endpoint
@app.post("/api/orders/create", response_model=OrderResponse)
async def create_order_endpoint(request: CreateOrderRequest):
    """
    Create a new Shopify order
    
    Example request:
    ```json
    {
        "line_items": [
            {
                "variant_id": 12345,
                "quantity": 1,
                "title": "Product Name",
                "price": 29.99
            }
        ],
        "customer_email": "customer@example.com",
        "financial_status": "paid",
        "test": true
    }
    ```
    """
    try:
        # Convert line items to list of dicts
        line_items_dict = [item.model_dump() for item in request.line_items]
        
        # Call MCP tool
        result_json = await create_order(
            line_items=line_items_dict,
            customer_email=request.customer_email,
            financial_status=request.financial_status,
            test=request.test
        )
        
        # Parse JSON response
        result = json.loads(result_json)
        
        return OrderResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return OrderResponse(
            success=False,
            data={},
            error=str(e)
        )

# Get Order Status Endpoint
@app.post("/api/orders/status", response_model=OrderResponse)
async def get_order_status_endpoint(request: GetOrderStatusRequest):
    """
    Get status of a Shopify order
    
    Example request:
    ```json
    {
        "order_id": 12345
    }
    ```
    """
    try:
        # Call MCP tool
        result_json = await get_order_status(order_id=request.order_id)
        
        # Parse JSON response
        result = json.loads(result_json)
        
        return OrderResponse(
            success=True,
            data=result
        )
    except Exception as e:
        return OrderResponse(
            success=False,
            data={},
            error=str(e)
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
