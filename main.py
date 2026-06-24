from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import os
import sys

# Add parent directory to path so imports work
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from copilot.engine import run_ordering_pipeline

app = FastAPI(
    title="Green Kitchen API",
    description="Backend API for Waste-Free B2B Replenishment Agent for Food Banks & Soup Kitchens (Agents for Good)",
    version="1.0"
)

# Enable CORS for frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ForecastRequest(BaseModel):
    day: str
    starting_stock: Dict[str, float]

class OrderItem(BaseModel):
    ingredient: str
    description: str
    sku: str
    cases: int
    cost: float

class ApproveRequest(BaseModel):
    items: List[OrderItem]

@app.get("/", response_class=HTMLResponse)
def read_root():
    try:
        index_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "static", "index.html")
        with open(index_path, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Error loading index.html</h1><p>{str(e)}</p>", 
            status_code=500
        )


@app.post("/forecast")
def calculate_forecast_order(req: ForecastRequest):
    day = req.day.lower()
    valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    if day not in valid_days:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid day '{req.day}'. Valid forecast days are: {', '.join(valid_days)}"
        )
        
    try:
        order_plan = run_ordering_pipeline(day, req.starting_stock)
        
        # Format response
        formatted_plan = []
        for item in order_plan:
            formatted_plan.append({
                "ingredient": item["ingredient"],
                "description": item["description"],
                "sku": item["sku"],
                "gross": round(item["gross"], 2),
                "stock": round(item["stock"], 2),
                "net": round(item["net"], 2),
                "cases": item["cases"],
                "unit": item["unit"],
                "surplus": round(item["surplus"], 2),
                "cost": round(item["cost"], 2)
            })
            
        return {
            "day": day,
            "draft_order": formatted_plan,
            "total_estimated_cost": round(sum(i["cost"] for i in formatted_plan), 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

@app.post("/approve")
def approve_draft_order(req: ApproveRequest):
    # This acts as our Human-in-the-Loop approval checkpoint.
    # It receives the Chef's finalized edits and mock-submits the cart to Sysco.
    if not req.items:
        raise HTTPException(status_code=400, detail="Cannot approve empty order list")
        
    ordered_items = [f"{item.sku} ({item.description}) x {item.cases}cs" for item in req.items if item.cases > 0]
    total_cost = sum(item.cost for item in req.items)
    
    print(f"\n[HUMAN-IN-THE-LOOP CHECKPOINT APPROVED]")
    for item in ordered_items:
        print(f" -> Sent to Supplier: {item}")
    print(f" -> Total Order Cost: ${total_cost:.2f}\n")
    
    return {
        "message": "Draft approved and sent to supplier cart successfully!",
        "item_count": len(ordered_items),
        "total_cost": round(total_cost, 2),
        "items_submitted": ordered_items
    }
